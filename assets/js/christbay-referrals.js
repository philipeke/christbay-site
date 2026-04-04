/**
 * ChristBay referral codes — localStorage on this origin, plus optional deployed manifest
 * (see /assets/data/referrals-public.json) so /join works for all visitors after you publish
 * an export. Global redemption caps still need a server if you must enforce them worldwide.
 */
(function (global) {
  'use strict';

  var STORAGE_KEY = 'christbay_referral_data_v1';
  var OVERLAY_EXTRA_KEY = 'christbay_referral_overlay_extra_v1';
  var SESSION_KEY = 'christbay_admin_session_ok';
  var PBKDF2_ITER = 120000;

  /** Codes loaded from referrals-public.json (in-memory). */
  var publicOverlay = [];

  function bufToB64(buf) {
    var bin = '';
    var bytes = new Uint8Array(buf);
    for (var i = 0; i < bytes.length; i++) bin += String.fromCharCode(bytes[i]);
    return btoa(bin);
  }

  function b64ToBuf(b64) {
    var bin = atob(b64);
    var bytes = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
    return bytes.buffer;
  }

  function randomId() {
    if (global.crypto && global.crypto.randomUUID) return global.crypto.randomUUID();
    return 'id-' + Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 12);
  }

  function normalizeCode(raw) {
    if (!raw || typeof raw !== 'string') return '';
    return raw.trim().toUpperCase().replace(/[^A-Z0-9-]/g, '');
  }

  function defaultState() {
    return {
      version: 1,
      admin: null,
      codes: [],
      redemptions: []
    };
  }

  function loadState() {
    try {
      var raw = global.localStorage.getItem(STORAGE_KEY);
      if (!raw) return defaultState();
      var data = JSON.parse(raw);
      if (!data || data.version !== 1) return defaultState();
      if (!Array.isArray(data.codes)) data.codes = [];
      if (!Array.isArray(data.redemptions)) data.redemptions = [];
      return data;
    } catch (e) {
      return defaultState();
    }
  }

  function saveState(state) {
    global.localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  }

  function timingSafeEqual(aB64, bB64) {
    try {
      var a = new Uint8Array(b64ToBuf(aB64));
      var b = new Uint8Array(b64ToBuf(bB64));
      if (a.length !== b.length) return false;
      var diff = 0;
      for (var i = 0; i < a.length; i++) diff |= a[i] ^ b[i];
      return diff === 0;
    } catch (e) {
      return false;
    }
  }

  async function deriveHash(password, saltBuffer) {
    var enc = new TextEncoder();
    var keyMaterial = await global.crypto.subtle.importKey(
      'raw',
      enc.encode(password),
      'PBKDF2',
      false,
      ['deriveBits']
    );
    var bits = await global.crypto.subtle.deriveBits(
      {
        name: 'PBKDF2',
        salt: saltBuffer,
        iterations: PBKDF2_ITER,
        hash: 'SHA-256'
      },
      keyMaterial,
      256
    );
    return bufToB64(bits);
  }

  async function setAdminPassword(password) {
    var salt = new Uint8Array(16);
    global.crypto.getRandomValues(salt);
    var hash = await deriveHash(password, salt);
    var state = loadState();
    state.admin = { saltB64: bufToB64(salt.buffer), hashB64: hash };
    saveState(state);
    return true;
  }

  async function verifyAdminPassword(password) {
    var state = loadState();
    if (!state.admin || !state.admin.saltB64 || !state.admin.hashB64) return false;
    var salt = b64ToBuf(state.admin.saltB64);
    var hash = await deriveHash(password, salt);
    return timingSafeEqual(hash, state.admin.hashB64);
  }

  async function changeAdminPassword(oldPassword, newPassword) {
    if (!(await verifyAdminPassword(oldPassword))) return false;
    return setAdminPassword(newPassword);
  }

  function hasAdminPassword() {
    var state = loadState();
    return !!(state.admin && state.admin.hashB64);
  }

  function setSession(ok) {
    if (ok) global.sessionStorage.setItem(SESSION_KEY, '1');
    else global.sessionStorage.removeItem(SESSION_KEY);
  }

  function isSessionValid() {
    return global.sessionStorage.getItem(SESSION_KEY) === '1';
  }

  function findCodeEntry(state, normalized) {
    for (var i = 0; i < state.codes.length; i++) {
      if (normalizeCode(state.codes[i].code) === normalized) return state.codes[i];
    }
    return null;
  }

  function getOverlayExtraMap() {
    try {
      var o = JSON.parse(global.localStorage.getItem(OVERLAY_EXTRA_KEY) || '{}');
      return o && typeof o === 'object' ? o : {};
    } catch (e) {
      return {};
    }
  }

  function incOverlayExtra(norm) {
    var m = getOverlayExtraMap();
    m[norm] = (m[norm] || 0) + 1;
    global.localStorage.setItem(OVERLAY_EXTRA_KEY, JSON.stringify(m));
  }

  function findRawOverlay(norm) {
    for (var j = 0; j < publicOverlay.length; j++) {
      if (normalizeCode(publicOverlay[j].code) === norm) return publicOverlay[j];
    }
    return null;
  }

  function buildRuntimeOverlayEntry(raw, norm) {
    var base = raw.usedCount || 0;
    var extra = getOverlayExtraMap()[norm] || 0;
    return {
      id: 'pub-' + norm,
      code: norm,
      label: raw.label || '',
      maxRedemptions: raw.maxRedemptions,
      usedCount: base + extra,
      expiresAt: raw.expiresAt,
      active: raw.active !== false
    };
  }

  function setPublicManifest(data) {
    publicOverlay = [];
    if (!data || !Array.isArray(data.codes)) return;
    for (var i = 0; i < data.codes.length; i++) {
      publicOverlay.push(data.codes[i]);
    }
  }

  function validateEntry(entry) {
    if (!entry || !entry.active) return { ok: false, reason: 'inactive' };
    if (entry.expiresAt) {
      var exp = new Date(entry.expiresAt).getTime();
      if (exp < Date.now()) return { ok: false, reason: 'expired' };
    }
    var max = entry.maxRedemptions;
    if (typeof max === 'number' && max > 0 && entry.usedCount >= max) {
      return { ok: false, reason: 'limit' };
    }
    return { ok: true };
  }

  function resolveForCheck(norm) {
    var state = loadState();
    var local = findCodeEntry(state, norm);
    if (local) return { entry: local, source: 'local' };
    var raw = findRawOverlay(norm);
    if (raw) return { entry: buildRuntimeOverlayEntry(raw, norm), source: 'overlay' };
    return null;
  }

  function checkCode(rawCode) {
    var norm = normalizeCode(rawCode);
    if (!norm) return { ok: false, reason: 'empty', normalized: '' };
    var r = resolveForCheck(norm);
    if (!r) return { ok: false, reason: 'unknown', normalized: norm };
    var v = validateEntry(r.entry);
    if (!v.ok) return { ok: false, reason: v.reason, entry: r.entry, normalized: norm };
    return { ok: true, entry: r.entry, normalized: norm };
  }

  function redeemCode(rawCode) {
    var norm = normalizeCode(rawCode);
    if (!norm) return { ok: false, reason: 'empty' };
    var state = loadState();
    var local = findCodeEntry(state, norm);
    var entry;
    var source;

    if (local) {
      entry = local;
      source = 'local';
    } else {
      var raw = findRawOverlay(norm);
      if (!raw) return { ok: false, reason: 'unknown' };
      entry = buildRuntimeOverlayEntry(raw, norm);
      source = 'overlay';
    }

    var v = validateEntry(entry);
    if (!v.ok) return { ok: false, reason: v.reason, entry: entry };

    if (source === 'local') {
      local.usedCount = (local.usedCount || 0) + 1;
    } else {
      incOverlayExtra(norm);
      entry = buildRuntimeOverlayEntry(findRawOverlay(norm), norm);
    }

    state.redemptions.unshift({
      id: randomId(),
      codeId: entry.id,
      codeSnapshot: norm,
      at: new Date().toISOString()
    });
    if (state.redemptions.length > 500) state.redemptions.length = 500;
    saveState(state);
    return { ok: true, entry: entry };
  }

  function listCodes() {
    return loadState().codes.slice();
  }

  function addCode(opts) {
    var state = loadState();
    var code = normalizeCode(opts.code || '');
    if (!code) return { ok: false, error: 'Code is required.' };
    if (findCodeEntry(state, code)) return { ok: false, error: 'That code already exists.' };
    if (findRawOverlay(code)) return { ok: false, error: 'That code exists in the published site manifest.' };
    var entry = {
      id: randomId(),
      code: code,
      label: (opts.label || '').trim() || 'Untitled',
      note: (opts.note || '').trim(),
      maxRedemptions: typeof opts.maxRedemptions === 'number' ? opts.maxRedemptions : 0,
      usedCount: 0,
      expiresAt: opts.expiresAt || null,
      active: opts.active !== false,
      createdAt: new Date().toISOString()
    };
    state.codes.push(entry);
    saveState(state);
    return { ok: true, entry: entry };
  }

  function updateCode(id, patch) {
    var state = loadState();
    for (var i = 0; i < state.codes.length; i++) {
      if (state.codes[i].id === id) {
        var e = state.codes[i];
        if (patch.label != null) e.label = String(patch.label).trim() || e.label;
        if (patch.note != null) e.note = String(patch.note).trim();
        if (patch.maxRedemptions != null) e.maxRedemptions = patch.maxRedemptions;
        if (patch.expiresAt !== undefined) e.expiresAt = patch.expiresAt || null;
        if (patch.active != null) e.active = !!patch.active;
        saveState(state);
        return { ok: true, entry: e };
      }
    }
    return { ok: false, error: 'Code not found.' };
  }

  function deleteCode(id) {
    var state = loadState();
    var next = [];
    for (var i = 0; i < state.codes.length; i++) {
      if (state.codes[i].id !== id) next.push(state.codes[i]);
    }
    if (next.length === state.codes.length) return { ok: false };
    state.codes = next;
    saveState(state);
    return { ok: true };
  }

  function getStats() {
    var state = loadState();
    var codes = state.codes;
    var active = 0;
    var totalUses = 0;
    for (var i = 0; i < codes.length; i++) {
      if (codes[i].active) active++;
      totalUses += codes[i].usedCount || 0;
    }
    var now = new Date();
    var monthStart = new Date(now.getFullYear(), now.getMonth(), 1).getTime();
    var redemptionsThisMonth = 0;
    for (var j = 0; j < state.redemptions.length; j++) {
      var t = new Date(state.redemptions[j].at).getTime();
      if (t >= monthStart) redemptionsThisMonth++;
    }
    return {
      totalCodes: codes.length,
      activeCodes: active,
      totalRedemptions: state.redemptions.length,
      totalUses: totalUses,
      redemptionsThisMonth: redemptionsThisMonth
    };
  }

  function getRedemptions(limit) {
    var n = limit || 50;
    var state = loadState();
    return state.redemptions.slice(0, n);
  }

  function exportJson() {
    return JSON.stringify(loadState(), null, 2);
  }

  function exportCodesPublic() {
    var state = loadState();
    return JSON.stringify(
      {
        version: 1,
        exportedAt: new Date().toISOString(),
        codes: state.codes.map(function (c) {
          return {
            code: c.code,
            label: c.label,
            maxRedemptions: c.maxRedemptions,
            usedCount: c.usedCount,
            expiresAt: c.expiresAt,
            active: c.active
          };
        })
      },
      null,
      2
    );
  }

  function importJson(jsonStr, replace) {
    var data = JSON.parse(jsonStr);
    if (!data || data.version !== 1) throw new Error('Invalid backup format.');
    if (!replace) {
      var cur = loadState();
      var ids = {};
      var codesSeen = {};
      for (var i = 0; i < cur.codes.length; i++) {
        ids[cur.codes[i].id] = true;
        codesSeen[normalizeCode(cur.codes[i].code)] = true;
      }
      for (var j = 0; j < data.codes.length; j++) {
        var cj = data.codes[j];
        var n = normalizeCode(cj.code);
        if (ids[cj.id] || codesSeen[n]) continue;
        ids[cj.id] = true;
        codesSeen[n] = true;
        cur.codes.push(cj);
      }
      cur.redemptions = (cur.redemptions || []).concat(data.redemptions || []);
      cur.redemptions.sort(function (a, b) {
        return new Date(b.at) - new Date(a.at);
      });
      if (cur.redemptions.length > 500) cur.redemptions.length = 500;
      saveState(cur);
    } else {
      saveState(data);
    }
  }

  function generateCodeSegment(len) {
    var chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
    var out = '';
    var bytes = new Uint8Array(len);
    global.crypto.getRandomValues(bytes);
    for (var i = 0; i < len; i++) out += chars[bytes[i] % chars.length];
    return out;
  }

  function suggestCode() {
    return generateCodeSegment(4) + '-' + generateCodeSegment(4);
  }

  global.ChristBayReferrals = {
    STORAGE_KEY: STORAGE_KEY,
    normalizeCode: normalizeCode,
    loadState: loadState,
    saveState: saveState,
    setAdminPassword: setAdminPassword,
    verifyAdminPassword: verifyAdminPassword,
    changeAdminPassword: changeAdminPassword,
    hasAdminPassword: hasAdminPassword,
    setSession: setSession,
    isSessionValid: isSessionValid,
    checkCode: checkCode,
    redeemCode: redeemCode,
    setPublicManifest: setPublicManifest,
    MANIFEST_URL: '/assets/data/referrals-public.json',
    loadPublicManifest: function () {
      return global.fetch('/assets/data/referrals-public.json', { cache: 'no-store' })
        .then(function (res) {
          if (!res.ok) return { ok: false };
          return res.json();
        })
        .then(function (data) {
          if (data) setPublicManifest(data);
          return { ok: true };
        })
        .catch(function () {
          return { ok: false };
        });
    },
    listCodes: listCodes,
    addCode: addCode,
    updateCode: updateCode,
    deleteCode: deleteCode,
    getStats: getStats,
    getRedemptions: getRedemptions,
    exportJson: exportJson,
    exportCodesPublic: exportCodesPublic,
    importJson: importJson,
    suggestCode: suggestCode,
    generateBulk: function (count, opts) {
      var added = [];
      var errors = 0;
      opts = opts || {};
      for (var i = 0; i < count; i++) {
        var tries = 0;
        var r;
        do {
          r = addCode({
            code: suggestCode(),
            label: (opts.labelPrefix ? String(opts.labelPrefix).trim() + ' ' : '') + 'Batch #' + (i + 1),
            maxRedemptions: typeof opts.maxRedemptions === 'number' ? opts.maxRedemptions : 0,
            active: true
          });
          tries++;
        } while (!r.ok && tries < 100);
        if (r.ok) added.push(r.entry);
        else errors++;
      }
      return { added: added, errors: errors };
    }
  };
})(typeof window !== 'undefined' ? window : this);

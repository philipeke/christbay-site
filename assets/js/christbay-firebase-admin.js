/**
 * Firebase web config for the admin UI only. Replace placeholders with your
 * project's values (Project settings → Your apps → Web app).
 * Firestore: create a document christbay_admins/{email_in_lowercase} before
 * first login (empty doc or { active: true }). Add the same email under
 * Authentication (Users) so password reset can be sent.
 *
 * Example security rule for that collection:
 *   match /christbay_admins/{emailId} {
 *     allow read: if request.auth != null
 *       && request.auth.token.email != null
 *       && request.auth.token.email.lower() == emailId;
 *   }
 */
(function (global) {
  'use strict';

  global.ChristBayFirebaseAdmin = {
    config: {
      apiKey: 'YOUR_API_KEY',
      authDomain: 'YOUR_PROJECT_ID.firebaseapp.com',
      projectId: 'YOUR_PROJECT_ID',
      storageBucket: 'YOUR_PROJECT_ID.appspot.com',
      messagingSenderId: 'YOUR_SENDER_ID',
      appId: 'YOUR_APP_ID'
    },
    adminsCollection: 'christbay_admins'
  };
})(typeof window !== 'undefined' ? window : this);

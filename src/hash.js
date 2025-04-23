const bcrypt = require('bcryptjs');

const plainPassword = 'admin';
const saltRounds = 10;

bcrypt.hash(plainPassword, saltRounds, (err, hash) => {
  if (err) {
    console.error('❌ Error hashing password:', err);
  } else {
    console.log('✅ Hashed password:', hash);
  }
});
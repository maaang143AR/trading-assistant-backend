// index.js
const express = require('express');
const cors = require('cors');
const app = express();
const PORT = 5000;
const { loginUser } = require('./controllers/authController.js');

app.use(express.json());
app.use(cors());



app.get('/', (req, res) => {
  res.send('Backend is running!');
});

app.post('/login', loginUser);

app.listen(PORT, () => {
  console.log(`Server is running on http://localhost:${PORT}`);
});

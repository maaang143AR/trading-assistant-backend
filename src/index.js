const express = require('express');
const cors = require('cors');
const app = express();
const PORT = 5000;
const { loginUser,fileUplaod } = require('./controllers/authController.js');
const verifyToken = require('./middleware/authMiddleware.js');
const { config } = require('dotenv');
const { spawn } = require('child_process');


// these lines are for python script execution
const python = spawn('python', ['src/ai_agent/gemini_agent.py']);

python.stdout.on('data', (data) => {
  console.log(`Python Output: ${data}`);
});

python.stderr.on('data', (data) => {
  console.error(`Python Error: ${data}`);
});

python.on('close', (code) => {
  console.log(`Python process exited with code ${code}`);
});

// End of python script execution
// Load environment variables from .env file
config();

app.use(express.json());
app.use(cors());
const multer = require('multer');

const prefix = 'dashboard/api';
const upload = multer({ dest: 'uploads/' }); // creates uploads folder if not exist

app.get('/', (req, res) => {
  res.send('Backend is running!');
});

app.post('/login', loginUser);
app.post(`/${prefix}/upload`,verifyToken, upload.single('file'), fileUplaod);

app.listen(PORT, () => {
  console.log(`Server is running on http://localhost:${PORT}`);
});

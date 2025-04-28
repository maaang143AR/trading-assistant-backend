const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const { config } = require('dotenv');
const { spawn } = require('child_process');
const readline = require('readline');
const path = require('path');
config();

const secretKey = process.env.JWT_SECRET // Replace


const Logincredentials = {
    username: 'admin',
    password: '$2b$10$S58yre8TWRV1Vyj/JiZeP.doi4hD9VW7eKxuOzBKb9/EfsiURr9J6' 
  }; 


  const loginUser = async (req, res) => { 
    let credentials = req.body;
    if(credentials.username !== Logincredentials.username) {
        res.status(401).json({ message: 'Invalid Username!' });
    }
    const isMatch = await bcrypt.compare(credentials.password, Logincredentials.password);
    if (!isMatch) {
        return res.status(401).json({ message: 'Invalid Password!' });
    }
    const token = jwt.sign({username: credentials.username}, secretKey, { expiresIn: '1h' });
    res.status(200).json({ message: 'Login successful!', token });
  }




async function fileUpload(req, res) {
  // 1) Validate
  if (!req.file || !req.body.message) {
    return res.status(400).json({
      status: 'error',
      message: 'Both a file and text field are required'
    });
  }
  // 2) Prepare the command
  const filePath = path.resolve(req.file.path);
  const command = {
    action: 'send_text_and_image',
    text: req.body.message,
    filePath
  };
  // 3) Locate your Python script
  const scriptPath = path.resolve(__dirname, '../ai_agent/gemini_agent.py');
  // 4) Spawn the Python agent (per request)
  const py = spawn('python', [scriptPath], {
    stdio: ['pipe', 'pipe', 'pipe']
  });
  // 5) Log any stderr from Python immediately
  py.stderr.on('data', chunk => {
    console.error('[PYTHON STDERR]', chunk.toString());
  });
  // 6) Read exactly one JSON line back
  const rl = readline.createInterface({
    input: py.stdout,
    crlfDelay: Infinity
  });
  let responded = false;
  // 7) Send our JSON command, then end stdin
  py.stdin.write(JSON.stringify(command) + '\n');
  py.stdin.end();
  // 8) Timeout guard (30s)
  const timeout = setTimeout(() => {
    if (responded) return;
    responded = true;
    rl.close();
    py.kill();
    res.status(504).json({ status: 'error', message: 'Python timed out' });
  }, 30000);
  // 9) Handle the first valid line from Python
  rl.on('line', line => {
    if (responded) return;
    responded = true;
    clearTimeout(timeout);
    rl.close();
    py.kill();
    let response;
    try {
      response = JSON.parse(line);
    } catch (err) {
      return res.status(502).json({
        status: 'error',
        message: 'Invalid JSON from Python',
        raw: line
      });
    }
    return res.json(response);
  });
  // 10) If Python exits/crashes before replying
  py.on('close', code => {
    if (responded) return;
    responded = true;
    clearTimeout(timeout);
    rl.close();
    const msg = code === 0
      ? 'Python exited without output'
      : `Python crashed (exit code ${code})`;
    return res.status(500).json({ status: 'error', message: msg });
  });
  // 11) If spawning Python itself fails
  py.on('error', err => {
    if (responded) return;
    responded = true;
    clearTimeout(timeout);
    return res.status(500).json({
      status: 'error',
      message: 'Failed to start Python',
      details: err.message
    });
  });
}
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  

    module.exports = { loginUser,fileUpload };
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const { config } = require('dotenv');
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


  const fileUplaod = (req, res) => {
    // return 'test';
    const file = req.file; // Assuming you're using multer for file uploads
    // return file
    if (!file) {
        return res.status(400).json({ message: 'No file uploadedssss!' });
    }
    console.log('File uploaded:', file);
    res.status(200).json({ message: 'File uploaded successfully!', file });
    
  }

    module.exports = { loginUser,fileUplaod };
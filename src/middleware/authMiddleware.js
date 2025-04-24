const jwt = require('jsonwebtoken');
const { config } = require('dotenv');
config();

const secretKey = process.env.JWT_SECRET; // Replace with your actual secret key

// const jwt = require('jsonwebtoken'); 
// const secretKey = process.env.JWT_SECRET;

const verifyToken = (req, res, next) => {   
    const authHeader = req.headers['authorization'];
    const token = authHeader && authHeader.split(' ')[1]; // "Bearer <token>"

    if (!token) {
        return res.status(401).json({ message: 'No token provided!' });
    }

    jwt.verify(token, secretKey, (err, decoded) => {
        if (err) {
            return res.status(401).json({ message: 'Unauthorized!' });
        }
        req.userId = decoded.id;
        next();
    });
};


module.exports = verifyToken;
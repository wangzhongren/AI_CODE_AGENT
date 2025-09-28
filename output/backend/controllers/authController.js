const jwt = require('jsonwebtoken');
const User = require('../models/User');

// Register new user
const register = async (req, res) => {
  try {
    const { username, email, password } = req.body;
    
    // Validate input
    if (!username || !email || !password) {
      return res.status(400).json({
        success: false,
        message: 'Username, email, and password are required'
      });
    }
    
    if (password.length < 6) {
      return res.status(400).json({
        success: false,
        message: 'Password must be at least 6 characters long'
      });
    }

    // Create user
    const userId = await User.create(username, email, password);
    const user = await User.findById(userId);
    
    // Generate JWT token
    const token = jwt.sign(
      { id: user.id, username: user.username },
      process.env.JWT_SECRET || 'your-secret-key',
      { expiresIn: '24h' }
    );
    
    res.status(201).json({
      success: true,
      data: {
        token,
        user: {
          id: user.id,
          username: user.username,
          email: user.email
        }
      }
    });
  } catch (error) {
    console.error('Error registering user:', error);
    
    if (error.message === 'User already exists') {
      return res.status(409).json({
        success: false,
        message: 'Username or email already exists'
      });
    }
    
    res.status(500).json({
      success: false,
      message: 'Internal server error'
    });
  }
};

// Login user
const login = async (req, res) => {
  try {
    const { identifier, password } = req.body;
    
    if (!identifier || !password) {
      return res.status(400).json({
        success: false,
        message: 'Username/email and password are required'
      });
    }

    const user = await User.findByCredentials(identifier, password);
    
    if (!user) {
      return res.status(401).json({
        success: false,
        message: 'Invalid credentials'
      });
    }

    // Generate JWT token
    const token = jwt.sign(
      { id: user.id, username: user.username },
      process.env.JWT_SECRET || 'your-secret-key',
      { expiresIn: '24h' }
    );
    
    res.json({
      success: true,
      data: {
        token,
        user: {
          id: user.id,
          username: user.username,
          email: user.email
        }
      }
    });
  } catch (error) {
    console.error('Error logging in:', error);
    res.status(500).json({
      success: false,
      message: 'Internal server error'
    });
  }
};

// Get current user profile
const getCurrentUser = async (req, res) => {
  try {
    const user = await User.findById(req.user.id);
    
    if (!user) {
      return res.status(404).json({
        success: false,
        message: 'User not found'
      });
    }
    
    res.json({
      success: true,
      data: {
        user: {
          id: user.id,
          username: user.username,
          email: user.email
        }
      }
    });
  } catch (error) {
    console.error('Error getting current user:', error);
    res.status(500).json({
      success: false,
      message: 'Internal server error'
    });
  }
};

module.exports = {
  register,
  login,
  getCurrentUser
};
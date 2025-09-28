const pool = require('../config/database');
const bcrypt = require('bcryptjs');

class User {
  // Create new user
  static async create(username, email, password) {
    // Check if user already exists
    const [existing] = await pool.execute(
      'SELECT id FROM users WHERE username = ? OR email = ?',
      [username, email]
    );
    
    if (existing.length > 0) {
      throw new Error('User already exists');
    }

    // Hash password
    const salt = await bcrypt.genSalt(10);
    const hashedPassword = await bcrypt.hash(password, salt);

    const [result] = await pool.execute(
      'INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
      [username, email, hashedPassword]
    );
    
    return result.insertId;
  }

  // Find user by username or email
  static async findByCredentials(identifier, password) {
    const [users] = await pool.execute(
      'SELECT id, username, email, password FROM users WHERE username = ? OR email = ?',
      [identifier, identifier]
    );
    
    if (users.length === 0) {
      return null;
    }

    const user = users[0];
    const isMatch = await bcrypt.compare(password, user.password);
    
    if (!isMatch) {
      return null;
    }

    return {
      id: user.id,
      username: user.username,
      email: user.email
    };
  }

  // Find user by ID
  static async findById(id) {
    const [users] = await pool.execute(
      'SELECT id, username, email FROM users WHERE id = ?',
      [id]
    );
    
    return users[0] || null;
  }
}

module.exports = User;
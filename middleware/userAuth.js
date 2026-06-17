const { getAuth } = require('../firebase')

const userAuth = async (req, res, next) => {
  const token = req.headers['authorization']?.split('Bearer ')[1]

  if (!token) {
    return res.status(401).json({ error: 'Missing token' })
  }

  try {
    const decoded = await getAuth().verifyIdToken(token)
    req.user = decoded
    next()

  } catch (error) {
    res.status(401).json({ error: 'Invalid token' })
  }
}

module.exports = userAuth
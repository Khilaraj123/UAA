// Sample Express application fixture for UAA testing
const express = require('express');
const app = express();
app.use(express.json());

const router = express.Router();

function requireAuth(req, res, next) {
    if (!req.headers.authorization) {
        return res.status(401).json({ error: 'Unauthorized' });
    }
    next();
}

app.get('/health', (req, res) => {
    res.json({ status: 'ok' });
});

router.get('/users', requireAuth, (req, res) => {
    res.json([{ id: 1, username: 'alice' }]);
});

router.get('/users/:id', requireAuth, (req, res) => {
    res.json({ id: req.params.id, username: 'alice' });
});

router.post('/users', requireAuth, (req, res) => {
    res.status(201).json({ id: 2, ...req.body });
});

app.use('/api/v1', router);

module.exports = app;


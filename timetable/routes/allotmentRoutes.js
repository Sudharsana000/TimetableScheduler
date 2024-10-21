const express = require('express');
const router = express.Router();

router.post('/addAllotments', (req, res) => {
    const allocationData = req.body;

    console.log(allocationData);

    res.status(200).json({ message: 'Data received and processed.' });
});

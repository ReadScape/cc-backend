const express = require("express");
const router = express.Router();
const userTagData = require("../services/userTagData");

/// get

router.get('/', async function(req, res, next) {
    try {
        res.json(await userTagData.getMultiple(req.query.page));
    } catch (err) {
        console.error(`Error while getting user tag data`, err.message);
        next(err);
    }
});

/// post

router.post('/', async function (req, res, next) {
    try {
        res.json(await userTagData.create(req.body));
    } catch (err) {
        console.error(`Error while creating user tag data`, err.message);
        next(err);
    }
});

/// update

/// delete

module.exports = router;
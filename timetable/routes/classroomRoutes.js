const express = require('express');
const classroomController = require('../controllers/classroomController');
const router = express.Router();

router.get('/', classroomController.getClassrooms);
router.post('/addrooms', classroomController.addClassroom);
router.put('/rooms/:hall_id', classroomController.updateClassroom);
router.delete('/deleterooms/:hall_id', classroomController.deleteClassroom);

module.exports = router;

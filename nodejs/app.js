const createError = require('http-errors');
const express = require('express');
const path = require('path');
const cookieParser = require('cookie-parser');
const logger = require('morgan');

const indexRouter = require('./ui/routes/index');
const apiRouter = require('./ui/routes/api');
const indyHandler = require('./indy/src/handler')({ defaultHandlers: true }); // () executes the function so that we can potentially have multiple indy handlers;

const app = express();

// view engine setup
app.set('views', path.join(__dirname, 'ui/views'));
app.set('view engine', 'ejs');

app.use(logger('dev'));
app.use(express.json());
app.use(express.urlencoded({ extended: false }));
app.use(cookieParser());
app.use(express.static(path.join(__dirname, 'ui/public')));

app.use('/', indexRouter);
app.use('/api', apiRouter);
app.post('/indy', indyHandler.middleware);

// catch 404 and forward to error handler
app.use(function(req, res, next) {
  next(createError(404));
});

// error handler
app.use(function(err, req, res, next) {
  // set locals, only providing error in development
  res.locals.message = err.message;
  res.locals.error = req.app.get('env') === 'development' ? err : {};

  // render the error page
  res.status(err.status || 500);
  res.render('error');
});

module.exports = app;

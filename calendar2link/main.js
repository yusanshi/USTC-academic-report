const args = require('minimist')(process.argv.slice(2));
const { google, outlook, office365, yahoo, ics } = require('calendar-link');

const event = {
  title: args['title'],
  description: args['description'],
  start: args['start'], //"2019-12-29 18:00:00 +0100",
  duration: [1, 'hour'],
};

const links = {
  google: google(event),
  outlook: outlook(event),
  office365: office365(event),
  yahoo: yahoo(event),
  ics: ics(event),
};

process.stdout.write(JSON.stringify(links));

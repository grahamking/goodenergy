/**
 * Good Energy Comment model
 */

if (typeof GOODENERGY == "undefined" || !GOODENERGY) {
    var GOODENERGY = {};
}

GOODENERGY.Comment = function(user, comment, when) {
	this.user = user;
	this.comment = comment;
	this.when = when;
}

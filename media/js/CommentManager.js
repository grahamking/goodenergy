/**
 * Good Energy CommentManager
 * Looks after the Comment objects.
 */

if (typeof GOODENERGY == "undefined" || !GOODENERGY) {
    var GOODENERGY = {};
}

GOODENERGY.CommentManager = function() {}

GOODENERGY.CommentManager.prototype = {

	/**
	 * Takes a JSON array representing a bunch of coments and returns an array of Comment objects
	 */
	getMany: function(commentJSONArray) {
		
		if (! commentJSONArray) {
			return [];
		}
	
		var comments = [];
		
		var userManager = GOODENERGY.userManager;
		
		for (var i=0, len=commentJSONArray.length; i<len; i++) {
			var jsonComment = commentJSONArray[i];
			var user = userManager.get(jsonComment.user);
			comments.push( new GOODENERGY.Comment(user, jsonComment.comment, new Date(jsonComment.created)) );
		}
		return comments;
	},
	
	create: function(comment) {
		var newComment = new GOODENERGY.Comment(
												GOODENERGY.currentUser,
												comment,
												new Date()
												);
		return newComment;
	}

}

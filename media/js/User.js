/**
 * Good Energy User model
 */

/* jslint config */
/*global GOODENERGY */

if (typeof GOODENERGY === "undefined" || !GOODENERGY) {
    window.alert('User.js: Requires GOODENERGY to be defined');
}

GOODENERGY.User = function(id, username, name, about, toMean, points, thumbURL, picURL) {
	this.id = id;
	this.username = username;
	this.name = name;
    this.label = name;  /* jQuery UI autocomplete needs this */
	this.about = about;

    /* How does this user, on aggregate, compare to the group average? One of LESS, AVRG, MORE */
	this.toMean = toMean;	

	this.points = points;
	this.thumbURL = thumbURL;
	this.picURL = picURL;
	
	this.indicators = [];
};
GOODENERGY.User.prototype = {
	
	toString: function() {
		return this.id;
	},

	/**
	 * User did something on the site, add a point.
	 */
	addPoint: function() {
		this.points++;
	},
	
	/**
	 * Is this user the current user?
	 */
	isCurrentUser: function() {
		return this.id === GOODENERGY.currentUser.id;
	},
	
	/**
	 * Display on screen, in profile popup.
	 */
	show: function() {
		var user = this,
            profileDialog;

        GOODENERGY.activeDashboard.createDialogs();

		$('#profile-dialog-msg').remove();	/* In case fadeOut didn't complete */

		profileDialog = $('#profile-dialog');
		profileDialog.html(GOODENERGY.Util.LOADING);
		profileDialog.dialog('option', 'title', this.name );
		profileDialog.dialog('open');
		
        profileDialog.load(
            '/users/'+ GOODENERGY.activeDashboard.campaignSlug +'/'+ this.username +'/',
            {},
            function(responseText, textStatus, xhr) { user.attachEventHandlers(); }
        );
        /*this.loadIndicators( onLoaded );*/
	},
	
    attachEventHandlers: function() {
        var user = this;

        $('#about_me_edit').submit(function(event){
            event.preventDefault();
            user.updateAbout(this);
        });

        $('#give_inspiration_point').submit(function(event){
            event.preventDefault();
            user.giveInspirationPoint(this);
        });

    },

    giveInspirationPoint: function(giveForm) {

        function onSuccess(result) {
            var jcredits = $('#insp_credits'),
                credits = $.trim( jcredits.text() ),
                jpoints = $('#insp_points'),
                points = $.trim( jpoints.text() );

            credits = Number(credits);
            points = Number(points);

            credits--;
            points++;

            jcredits.text(credits);
            jpoints.text(points);

            $(giveForm).hide().next().show();
        }

        GOODENERGY.Util.postForm(giveForm, onSuccess, 'text');
    },

	/**
	 * Send the new About Me text to the server
	 */
	updateAbout: function(aboutForm) {
	
        GOODENERGY.Util.postForm(aboutForm, function(data){}, 'text');

		if ( ! $('#profile-dialog-msg').length ) {
			$('#about_me_edit').append('<strong id="profile-dialog-msg">Saved</strong>');
			$('#profile-dialog-msg').fadeOut(5000);
		}
	}
	
};

/**
 * Good Energy UserManager
 * Looks after users and profiles objects.
 *
 * @requires GOODENERGY
 */

/* jslint config */
/*globals GOODENERGY */

if (typeof GOODENERGY === "undefined" || !GOODENERGY) {
    window.alert('UserManager requires Dashboard to define GOODENERGY');
}

GOODENERGY.UserManager = function() {
    this.userArray = [];
    $('#af_user_display').one('focus', $.proxy(this.loadUsers, this) );
};

GOODENERGY.UserManager.prototype = {
	
    /**
     * Ajax fetch list of users.
     */
    loadUsers: function() {
        var url = '/'+ GOODENERGY.activeDashboard.campaignSlug +'/campaigns/users/all.json';
        $.getJSON(url, {}, $.proxy(this.onLoadUsers, this));
    },

	/**
	 * Called once the JSON load of all the users completes. Stores the users in memory by id.
	 */
	onLoadUsers: function(usersJSON) {
        this.userArray = usersJSON;
		this.attachEventHandlers();
	},

	/**
	 * Events handlers that don't belong to an individual User
	 */
	attachEventHandlers: function() {
		var userManager = this;
		
		$('#af_user_display').autocomplete({
			source: userManager.userArray,
            select: function(event, ui) { 
                $('#af_user_id').val(ui.item.id); 
                $('#filter_activity').submit();
            }
		});
	},

    /**
     * Display a user profile
     */
    showUserAtURL: function(url) {
		var profileDialog, userManager = this;

        GOODENERGY.activeDashboard.createDialogs();

		$('#profile-dialog-msg').remove();	/* In case fadeOut didn't complete */

		profileDialog = $('#profile-dialog');
		profileDialog.html(GOODENERGY.Util.LOADING);
		profileDialog.dialog('open');

        $.getJSON(url, {}, function(data, textStatus) {
		    profileDialog.dialog('option', 'title', data.name );
            profileDialog.html(data.html);
            userManager.attachProfileEventHandlers();
        });
    },

    /**
     * Event handlers for profile.
     */
    attachProfileEventHandlers: function() {

        var userManager = this;

        $('#about_me_edit').submit(function(event){
            event.preventDefault();
            userManager.updateAbout(this);
        });

        $('#give_inspiration_point').submit(function(event){
            event.preventDefault();
            userManager.giveInspirationPoint(this);
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

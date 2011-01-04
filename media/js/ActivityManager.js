/**
 * Good Energy ActivityManager model
 * @requires GOODENERGY
 */

/* jslint config */
/*global GOODENERGY */

if (typeof GOODENERGY === "undefined" || !GOODENERGY) {
    window.alert('ActivityManager required GOODENERGY to be already defined');
}

GOODENERGY.ActivityManager = function() {
	
	this.activities = [];
	this.recent = [];
	this.attachEventHandlers();
};

GOODENERGY.ActivityManager.prototype = {
	
	/**
	 * Events handlers that don't belong to an individual Activity
	 */
	attachEventHandlers: function() {
		var activityManager = this,
            STATUS_UPDATE_MAX = 250;
				
		$('#idea_form').submit(function(event){
			event.preventDefault();
			activityManager.newStatus(this);
		});
		
		$('#view_recent_activity').click(function(event){
			event.preventDefault();
			activityManager.showRecent();			
		});
	    $('#view_my_activity').click(function(event){
            event.preventDefault();
            activityManager.showMine( $(this) );
        });

		$('#filter_activity input').click(function(event){
			event.preventDefault();
			activityManager.showFiltered();
		});
		
        $('#filter_activity').submit(function(event) { activityManager.filter(event); });

        $('#community').click(function(event) { activityManager.handleActivityClick(event); });

        $('form.status textarea').autogrow();
        $('#status_field').keyup(function(){
            var currentVal = $(this).val(),
                remain = STATUS_UPDATE_MAX - currentVal.length;
            if ( remain < 0 ) {
                remain = 0;
                $(this).val( currentVal.substring(0, STATUS_UPDATE_MAX) );
            }
            if (remain % 10 === 0 || remain < 10) {
                $('#status_remaining_chars').text(remain +' characters left');
            }
        });

        $('.status_actions a').click(function(event){
            event.preventDefault();
            var obj_type = $(this).attr('id').split('_')[1];
            $('form.status').hide();
            $('#'+ obj_type +'_form').show();
        });

        GOODENERGY.Util.attachClearField( $('#community') );
	},

    /**
     * User clicked somewhere in the activity feed
     */
    handleActivityClick: function(event) {

        var target = $(event.target),
            userId,
            url,
            loading,
            urlParts,
            count;

        if ( target.hasClass('comment_link') ) { 
            event.preventDefault();
            this.toggleComments(target);
        }
        else if ( target.hasClass('like_link') || target.hasClass('unlike_link') ) {
            event.preventDefault();
            GOODENERGY.Util.toggleLike(target, 'activity');
        }
        /*
        else if ( target.is('a.profile_link') ) {
            event.preventDefault();
            GOODENERGY.userManager.showUserAtURL(target.attr('href'));
        }
        else if ( target.parent().is('a.profile_link') ) {
            event.preventDefault();
            GOODENERGY.userManager.showUserAtURL(target.parent().attr('href'));
        }
        */
        else if (target.hasClass('action_on_change')) {
            event.preventDefault();
        }
        else if (target.hasClass('clear_field')) {
            target.val('');
        }
        else if (target.hasClass('comment_submit')) {
            event.preventDefault();
            GOODENERGY.Util.submitComment(target, 'activity');
        }
        else if (target.hasClass('delete_comment')) {
            event.preventDefault();
            GOODENERGY.Util.deleteComment(target, 'FeedEntry');
        }

        else if (target.is('#more_activity')) {
            event.preventDefault();
            url = target.attr('href') ;

            loading = $('<div></div>');
            target.before(loading);
            loading.html(GOODENERGY.Util.LOADING);

            $.getJSON(
                url, 
                {},
                function(data, textStatus) { 
                    loading.html(data.html);
                    if (data.is_done) {
                        target.remove();
                    }
                });

            urlParts = url.split('=');
            count = window.parseFloat(urlParts[1]) + 10;
            target.attr('href', urlParts[0] +'='+ count);
        }

    },

    /**
     * Toggle display of the comments section for the given id
     */
    toggleComments: function(commentLink) {

        var comments = commentLink.closest('.activity').find('.comments');
        if (comments.is(':visible')) {
            comments.hide();
        }
        else {
            comments.show();
            $('textarea', comments).autogrow();
        }
    },

	/**
	 * User entered status update
	 */
	newStatus: function(statusForm) {
		
		/* Check they didn't click 'Share' before typing anything */
		if ($('#idea_form textarea').hasClass('inactive')) {
			$('#idea_form textarea').text('Click here and share your thoughts');
			return;
		}
		
		var form = $(statusForm),
		    currentUser = GOODENERGY.currentUser,
            data,
            target;

		$('#idea_form input[type="submit"]').attr('disabled', 'disabled');
        form.parent().after(
                '<div id="loading_status">'+
                    '<img src="/media/images/ajax-loader.gif" />'+
                '</div>');

		data = form.serialize();
		target = form.attr('action');

		$.post(target, 
				data, 
				function(data, textStatus) {
                    $('#loading_status').replaceWith(data);	
					$('#idea_form textarea').val('');
					$('#idea_form input[type="submit"]').attr('disabled', '');
				}, 
				"html");
	},
	
	get: function(activityId) {
		return this.activities[activityId];
	},

	/**
	 * Switch to the 'Recent' tab
	 */
	showRecent: function() {
		$('#view_recent_activity').parent().addClass('active');
		$('#recent_activity').show();		

		$('#filter_activity input').removeClass('active');
		$('#view_my_activity').parent().removeClass('active');
		$('#filtered_activity').hide();
        $('#my_activity').hide();
	},
	
    /**
     * Switch to the 'Mine' tab
     */
    showMine: function(link) {

        var url = link.attr('href');
        
		$('#view_my_activity').parent().addClass('active');
        $('#my_activity').load(url).show();

        $('#view_recent_activity').parent().removeClass('active');
		$('#filter_activity input').removeClass('active');
		$('#recent_activity').hide();		
		$('#filtered_activity').hide();
    },

	/**
	 * Switch to the search results tab
	 */
	showFiltered: function() {
		$('#filter_activity input').addClass('active');
		$('#filtered_activity').show();

		$('#view_recent_activity').parent().removeClass('active');
		$('#view_my_activity').parent().removeClass('active');
		$('#recent_activity').hide();
		$('#my_activity').hide();
	},

	/**
	 * Show only activies for a specific user
	 */
	filter: function(event) {
		event.preventDefault();
		
		var userId = $('#af_user_id').val(),
            url = $(event.target).attr('action') +'?user_id='+ userId;
		if (! userId) { return; }

        $('#filtered_activity').html(GOODENERGY.Util.LOADING).load(url);
	}
	
};


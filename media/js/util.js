/** GOOD ENERGY utility methods 
 *
 * @requires GOODENERGY
 */

/* jslint config */
/*global GOODENERGY */

/**
 ** Extend Array built-in
 **/
Array.max = function( array ){
    return Math.max.apply( Math, array );
};

Array.min = function( array ){
    return Math.min.apply( Math, array );
};
/* Array Remove - By John Resig (MIT Licensed) */
Array.prototype.remove = function(from, to) {
  var rest = this.slice((to || from) + 1 || this.length);
  this.length = from < 0 ? this.length + from : from;
  return this.push.apply(this, rest);
};

/* Simple JavaScript Templating
 John Resig - http://ejohn.org/ - MIT Licensed
 http://ejohn.org/blog/javascript-micro-templating/
*
(function(){
var cache = {};

this.tmpl = function tmpl(str, data){
 // Figure out if we're getting a template, or if we need to
 // load the template - and be sure to cache the result.
 var fn = !/\W/.test(str) ?
   cache[str] = cache[str] ||
     tmpl(window.document.getElementById(str).innerHTML) :
  
   // Generate a reusable function that will serve as a template
   // generator (and which will be cached).
   new Function("obj",
     "var p=[],print=function(){p.push.apply(p,arguments);};" +
    
     // Introduce the data as local variables using with(){}
     "with(obj){p.push('" +
    
     // Convert the template into pure JavaScript
     str
       .replace(/[\r\t\n]/g, " ")
       .split("<%").join("\t")
       .replace(/((^|%>)[^\t]*)'/g, "$1\r")
       .replace(/\t=(.*?)%>/g, "',$1,'")
       .split("\t").join("');")
       .split("%>").join("p.push('")
       .split("\r").join("\\'")
   + "');}return p.join('');");

 // Provide some basic currying to the user
 return data ? fn( data ) : fn;
};
})();
*/

/*
 * Auto-growing textareas
 * From javascripty.com
 */
(function($) {
    $.fn.autogrow = function(options) {
        
        this.filter('textarea').each(function() {
            
        var $this       = $(this),
            minHeight   = $this.height(),
            lineHeight  = $this.css('lineHeight'),
            shadow,
            update,
            /* for update function */
            val,
            newHeight;

            shadow = $('<div></div>').css({
                position:   'absolute',
                top:        -10000,
                left:       -10000,
                width:      $(this).width(),
                fontSize:   $this.css('fontSize'),
                fontFamily: $this.css('fontFamily'),
                lineHeight: $this.css('lineHeight'),
                resize:     'none'
            }).appendTo(window.document.body);
            
            update = function() {
                
                val = this.value.replace(/</g, '&lt;')
                                    .replace(/>/g, '&gt;')
                                    .replace(/&/g, '&amp;')
                                    .replace(/\n/g, '<br/>');
                shadow.html(val);

                newHeight = Math.max(shadow.height() + 20, minHeight);
                $(this).css('height', newHeight);
            };
 
            $(this).change(update).keyup(update).keydown(update);
            
        });
        
        return this;
    };
    
})(jQuery);

/**
 ** Our methods
 **/

if (typeof GOODENERGY === "undefined" || !GOODENERGY) {
    window.alert('Requires GOODENERGY to be already defined');
}

GOODENERGY.Util = {

    LOADING: '<img width="16" height="16" src="/media/images/ajax-loader.gif" alt="Loading" />',

    /**
     * Like the django tag - give it a number, returns 's' if the number is not 1
     */
    pluralize: function(val) {
        return val !== 1 ? 's' : '';
    },

    /**
     * Ajax submit a form
     * @param callback Function to call on success. Gets given the 'data'
     * element returned by jQuery.
     * @param format One of the jQuery formats: json, html, text, etc
     */
    postForm: function(formDOM, callback, format) {

        var form = $(formDOM),
            data = form.serialize(),
            target = form.attr('action');
        $.post(	target, 
                data, 
                function(data, textStatus) { callback(data); },
                format);
    },

    /**
     * Record and display that current user likes or doesn't like an activity or change
     */
    toggleLike: function(likeUnlikeLink, parentClass) {

        var parent = likeUnlikeLink.closest('.'+ parentClass),
            likeLink,
            unLikeLink,
            like,
            likeParent,
            unlikeDisplay,
            url;

        /* Swap the links */
        likeLink = parent.find('.like_link');
        unLikeLink = parent.find('.unlike_link');

        if ( likeLink.is(':visible') ) {
            like = true;
            likeLink.hide();
            unLikeLink.show();
        }
        else {
            like = false;
            unLikeLink.hide();
            likeLink.show();
        }

        /* Swap the user displays */
        likeParent = parent.find('.like_this');
        likeParent.show();
        likeParent.find('.like').hide();
        if (like) {
            likeParent.find('.i_like').show();
        }
        else {
            /* Display the others who like, if there are others */
            unlikeDisplay = likeParent.find('.i_unlike');
            if ( jQuery.trim(unlikeDisplay.text()).length === 0 ) {
                likeParent.hide();
            }
            else {
                unlikeDisplay.show();
            }
        }

        /* Fire the ajax server update */
        url = likeUnlikeLink.attr('href');
        $.post(url, 
                [],
                function(data, textStatus) { },
                "text");

    },

    /**
     * Delete a comment.
     * @param submitLink  jQuery object of the link that was clicked
     */
    deleteComment: function(submitLink) {
        var url = submitLink.attr('href'),
            comment = submitLink.closest('.FeedEntry'),
            /* For decrementing comment count */
            parent,
            commentCount,
            commentLink;

        $.post(url,
               {},
               function(data, textStatus) { },
               'text/html');

        comment.hide();

        /* Decrement comment count */
        parent = comment.closest('.activity');

        commentCount = parseInt( parent.find('.comment_count').text(), 0 );
        commentCount--;

        commentLink = parent.find('.comment_link');
        commentLink.html(
            '<span class="comment_count">'+ 
            commentCount +'</span> comment'+ 
            GOODENERGY.Util.pluralize(commentCount)
            );
    },

    /**
     * Add new comment on Activity or Change
     */
    submitComment: function(submitButton, parentClass) {

        var form, container, data, target, parent, commentCount, commentLink;

        function displayNewComment(data, textStatus) {
            submitButton.attr('disabled', '');
            $('#loading_comment').replaceWith(data);

            form.find('textarea').val('');
        }

        submitButton.attr('disabled', 'disabled');
        form = $( submitButton.closest('form') );

        container = form.closest('.FeedEntry');
        container.before(
            '<div id="loading_comment">'+
                '<img src="/media/images/ajax-loader.gif" />'+
            '</div>');

        data = form.serialize();
        target = form.attr('action');
        $.post(	target, 
                data, 
                displayNewComment,
                "html");

        /* Increase comment count */
        if (parentClass) {
            parent = container.closest('.'+ parentClass);

            commentCount = parseInt( parent.find('.comment_count').text(), 0 );
            commentCount++;

            commentLink = parent.find('.comment_link');
            commentLink.html(
                '<span class="comment_count">'+ 
                commentCount +'</span> comment'+ 
                GOODENERGY.Util.pluralize(commentCount)
                );
        }
    },

    /**
     * Takes a string, and if it is longer than 'len' characters, splits
     * it by replacing the middle space with a <br/> tag. Keeps splitting
     * until each section is shorther than len.
     * If there's no space in the string, splits in the exact middle and 
     * adds a hyphen.
     */
    cleverSplit: function(str, len) {

        var length, middle, left, right, midChar, split, offset, beforeMid, afterMid;

        if (typeof(str) !== 'string') { return str; }

        str = $.trim(str);
        if ( str.length <= len ) { return str; }

        length = str.length;
        middle = Math.floor(length / 2);

        if ( str.indexOf(' ') === -1 ) {
            left = str.substring(0, middle) +'-';
            right = str.substring(middle, length);
        }
        else {

            midChar = str.charAt(middle);
            if (midChar === ' ') {
                split = middle;
            }
            else {
                offset = 0;
                do {

                    offset++;
                    if (middle - offset >= 0) {
                        beforeMid = str.charAt(middle - offset);
                    }
                    if (middle + offset < length) {
                        afterMid = str.charAt(middle + offset);
                    }

                } while (beforeMid !== ' ' && afterMid !== ' ' && offset <= middle);

                if (beforeMid === ' ') {
                    split = middle - offset;
                }
                else if (afterMid === ' ') {
                    split = middle + offset;
                }

            }

            left = str.substring(0, split);
            right = str.substring(split, length);

        }

        return GOODENERGY.Util.cleverSplit(left, len) +'<br/>'+ 
                GOODENERGY.Util.cleverSplit(right, len);
    },

    /**
     * Form fields below 'context' with .clear_field will have their text removed on first click 
     */
    attachClearField: function(context) {
    
		$(context).click(function(event){
            var target = $(event.target);
            if (target.hasClass('clear_field')) {
                target.val('');
				target.removeClass('inactive');
                target.removeClass('clear_field');
			}
		});
		
    }

}; /* End GOODENERGY.Util */


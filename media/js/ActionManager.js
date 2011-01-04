/** Client side code for Action objects
 *
 * @requires GOODENERGY, GOODENERGY.Dashboard, GOODENERGY.Util
 */

/* jslint config */
/*global GOODENERGY */

if (typeof GOODENERGY === "undefined" || !GOODENERGY) {
    window.alert('ActionManager needs Dashboard and Util');
}

GOODENERGY.ActionManager = function() {

    var actionContainer = $('#actions');
    this.attachEventHandlers( actionContainer );

    /* Show first action */
    this.toggleDisplay( $('.action', actionContainer)[0] );
};

GOODENERGY.ActionManager.prototype = {

    attachEventHandlers: function(context) {
        var actionManager = this;
        context.click(function(event) {actionManager.handleActionClick(event);} );
        context.submit(function(event) {actionManager.handleActionSubmit(event);} );

        $('#view_all_actions').click(function(event){ actionManager.showTab(event, 'all_actions', this); });
        $('#view_my_actions').click(function(event){ actionManager.showTab(event, 'my_actions', this); });
        $('#view_popular_actions').click(function(event){ actionManager.showTab(event, 'popular_actions', this); });

        $('#search_actions').submit(function(event){
            event.preventDefault();
            actionManager.search();
        });

        GOODENERGY.Util.attachClearField( $('#search_actions') );
    },

    /**
     * Search actions and display result.
     */
    search: function() {

        $('#actions .TitleOptions li').removeClass('active'); 
        $('#actions .action_tabsheet').hide();
        $('#search_results_actions').html(GOODENERGY.Util.LOADING).show();

        var form = $('#search_actions');
        GOODENERGY.Util.postForm(
            form,
            function(data) { $('#search_results_actions').html(data); },
            'html');
    },

    /**
     * Show one of the All Pledges / Popular Pledges / My Pledges tabs.
     */
    showTab: function(event, name, linkDOMParam) {

        var linkDOM = $(linkDOMParam), 
            url = linkDOM.attr('href'),
            tab;

        event.preventDefault();

        // Tab header
       $('#actions div.TitleOptions li').removeClass('active');
       linkDOM.parent().addClass('active');

        // Tab content
        $('#actions .action_tabsheet').hide();
        tab = $('#'+ name).show();

        if (url.length > 1) {
            tab.load(url);
        }
    },

    /**
     * Submit a form anywhere in an action - event delegation
     */
    handleActionSubmit: function(event) {

        var actionManager = this,
            target = $(event.target),
            parent = target.parent();

        event.preventDefault();

        if (target.is('form.barriers')) {
            parent.html(GOODENERGY.Util.LOADING);
            GOODENERGY.Util.postForm(
                target,
                function(data){ parent.html(data); },
                'text/html');
        }
        else if (target.is('form.pledge, form.done_it')) {
            GOODENERGY.Util.postForm(
                    target, 
                    function(data) { 
                        actionManager.onFullAction(data, target.closest('.action'));
                    },
                    'text/html');
        }
    },

    /**
     * Click anywhere in an action - event delegation.
     */
    handleActionClick: function(event) {

        var actionManager = this,
            target = $(event.target),
            parent,
            action,
            /* used by obstacle_link */
            barriersContainer;

        parent = target.parent();

        if (parent.hasClass('action_title') || parent.parent().hasClass('action_title')) {
            event.preventDefault();
            actionManager.toggleDisplay( target.closest('.action') );
        }
        else if (target.hasClass('submit_form')) {
            event.preventDefault();
            parent.submit();
        }
        else if (target.hasClass('obstacle_link')) {
            event.preventDefault();
            action = target.closest('div.action');
            barriersContainer = $('form.barriers', action);
            if (barriersContainer.is(':visible')) {
                barriersContainer.hide();
            }
            else {
                $('div.action_body', action).show();
                barriersContainer.show();
            }
        }
        else if (target.hasClass('action_learn')) {
            event.preventDefault();
            action = target.closest('div.action');
            GOODENERGY.activeDashboard.createDialogs();
            $('#action-learn-dialog')
                .html( $('.learn_contents', action).html() )
                .dialog('option', 'title', $('.action_title a', action).text() )
                .dialog('open');
        }
        /*
        else if (target.is('a.profile_link')) {
            event.preventDefault();
            GOODENERGY.userManager.showUserAtURL(target.attr('href'));
        }
        else if (parent.is('a.profile_link')) {
            event.preventDefault();
            GOODENERGY.userManager.showUserAtURL(target.parent().attr('href'));
        }
        */
    },

    /**
     * Expand or contract an Action
     */
    toggleDisplay: function(domParam) {
        var actionManager = this,
            dom = $(domParam),
            actionId,
            newDom;

        dom.find('.full_action').toggle();
        dom.find('.basic_action').toggle();
    },

    onFullAction: function(data, domParam) {
        var dom = $(domParam),
            newDom = $(data);

        dom.replaceWith(newDom); 
        this.attachEventHandlers(newDom);
        /*GOODENERGY.activeDashboard.attachClearField(newDom);*/
        $('textarea', newDom).autogrow();

        return newDom;
    }

};


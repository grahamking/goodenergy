/**
 * Good Energy dashboard controller
 * @requires GOODENERGY
 */

/* jslint config */
/*global GOODENERGY */

if (typeof GOODENERGY === "undefined" || !GOODENERGY) {
    window.alert('GOODENERGY variable needs to be defined');
}

GOODENERGY.ONE_DAY_MILLIS = 24 * 3600 * 1000;
GOODENERGY.ONE_WEEK_MILLIS = 7 * GOODENERGY.ONE_DAY_MILLIS;
GOODENERGY.ONE_MONTH_MILLIS = 30 * GOODENERGY.ONE_DAY_MILLIS;

GOODENERGY.Dashboard = function() {

    this.isResultState = GOODENERGY.DATA.isDone;	
    this.hasGraph = GOODENERGY.DATA.hasGraph;

    this.campaignSlug = GOODENERGY.DATA.campaignSlug;

	GOODENERGY.userManager = new GOODENERGY.UserManager();	
    GOODENERGY.activityManager = new GOODENERGY.ActivityManager();
    GOODENERGY.actionManager = new GOODENERGY.ActionManager();

    if (this.hasGraph) {
        this.indicator = new GOODENERGY.Indicator( GOODENERGY.DATA.indicator );
    }
    
	this.isBarGraphAverage = true;	    /* Display the aggregate average data on the bar graph */ 
	this.isLineGraphAverage = false;	/* Display the aggregate average data on the line graph */ 
	
    /* Expand dates so that first and last appear on graph */
    if (this.hasGraph) {
        this.campaignStartDate = 
            this.graphStartDate = GOODENERGY.DATA.graph.start_date - GOODENERGY.ONE_DAY_MILLIS;
        this.campaignEndDate = 
            this.graphEndDate = GOODENERGY.DATA.graph.end_date + GOODENERGY.ONE_DAY_MILLIS;
    }

    if (this.isResultState) {
        this.attachAnswerEventHandlers();
        this.displayLineGraph(this.currentIndicator());
    }
    else {
        this.attachQuestionEventHandlers();
        this.displayBarGraph(this.currentIndicator());
    }

    this.hasDialogs = false;

    if (GOODENERGY.DATA.isNewUser) {
        this.showInitialSurvey();
    }
};

GOODENERGY.Dashboard.prototype = {

    /**
     * Set the indicators answer data
     */
    updateAnswers: function(jsonAnswersArray) {
        var i = 0,
            answer = null,
            indicator = null;

        for (i=0; i< jsonAnswersArray.length; i++) {
            answer = jsonAnswersArray[i];
            indicator = this.indicatorsById[answer.indicator_id];
            indicator.updateAnswers(answer);
        }

    },

	/**
	 * Creates the jQuery UI dialogs, ready for action
	 */
	createDialogs: function() {
		 
        if (this.hasDialogs) {
            return;
        }

		$('#profile-dialog').dialog({ 
			autoOpen: false,
			modal: true,
			width: 440,
			height: 650,
            buttons: {},
			closeOnEscape: true,
			resizable: false
		});

        $('#settings-dialog').dialog({
            autoOpen: false,
            modal: true,
            width: 400,
            height: 550,
            closeOnEscape: true,
            resizable: false
        });
        
        $('#survey-dialog').dialog({
            autoOpen: false,
            modal: true,
            width: 400,
            height: 320,
            closeOnEscape: true,
            resizable: false
        });

        $('#action-learn-dialog').dialog({
            autoOpen: false,
            modal: true,
            width: 500,
            height: 300,
            closeOnEscape: true,
            resizable: false
        });

        $('#invite-dialog').dialog({
            autoOpen: false,
            modal: true,
            width: 550,
            height: 175,
            closeOnEscape: true,
            resizable: false
        });

        this.hasDialogs = true;
	},	
		
	currentIndicator: function() {
        return this.indicator;
	},
	
	/**
	 * Show the line graph for given indicator.
	 */
	displayLineGraph: function(indicator) {

        if (! this.hasGraph) {
            return;
        }

        var userValues, avgValues, i, len;

		if (this.isLineGraphAverage) {
			userValues = indicator.userAvgData;
		    avgValues = indicator.meanAvgData;
		}
		else {
			userValues = indicator.userData;
			avgValues = indicator.meanData;
		}
         
        for (i=0, len=indicator.valueLabels.length; i<len; i++) {
            indicator.valueLabels[i] = GOODENERGY.Util.cleverSplit(indicator.valueLabels[i], 10);
        }

		GOODENERGY.Graph.populateGraph(
                "graph",        // id of the canvas placeholder
			    userValues,
			    avgValues,
			    null,       // id of the legend
			    "Me",
			    indicator.userAverage,
                indicator.groupAverage,               // the norm for this indicator
                this.graphStartDate,
                this.graphEndDate,
			    'After you have answered some questions, your results will appear here',
			    indicator.valueTicks,
			    indicator.valueLabels,
			    indicator.hoverLabels
			  );
	},

	/**
	 * Show the bar graph for given indicator.
	 */
    displayBarGraph: function(indicator) {

        if (! this.hasGraph) {
            return;
        }

        var userValues, avgValues, graphOptions, 
            userVal,
            increment = 1,
            maxVal,
            valueLabels = [],
            userPrevious,
            avgVal, 
            avgPrevious,
            userDir = '', 
            avgDir = '';

		if (this.isBarGraphAverage) {
			userValues = indicator.userAvgData;
		    avgValues = indicator.meanAvgData;
		}
		else {
			userValues = indicator.userData;
			avgValues = indicator.meanData;
		}

        if (userValues.length !== 0) {
            userVal = userValues[userValues.length - 1][1];
        }
        else {
            userVal = 0;
        }

        if (avgValues.length !== 0) {
            avgVal = avgValues[avgValues.length - 1][1];
        }
        else {
            avgVal = 0;
        }

        if (indicator.type !== 'number') { /* Graph lib will put in numbers for us */
            valueLabels = indicator.valueLabels;
        }

        if (indicator.type === 'likert') {
            maxVal = indicator.valueLabels.length + 1;
        }
        else {
            maxVal = Math.max(userVal, avgVal) + 1;
        }

        graphOptions = {
            maxValue: maxVal,
			padding: 30,
            paddingLeft: 40,
			outline: true,
			one: { color: '#E8C149', legend: 'Me', legendColor: 'black' },
			two: { color: '#60BEFF', legend: 'Group<br/> average', legendColor: 'black' },
            background: { 
                color: 'white', 
                lines: true, 
                lineColor: '#ede',
                lineLabels: valueLabels,
                lineIncrement: 1,
                lineLabelsColor: '#666'
            }
        };

        if (userValues.length > 1) {
            userPrevious = userValues[userValues.length - 2][1];
            userDir = userPrevious < userVal ? 'up' : 'down';
            graphOptions.oneArrow = { direction: userDir, outline: false, opacity: 0.3 };
        }
        if (avgValues.length > 1) {
            avgPrevious = avgValues[avgValues.length - 2][1];
            avgDir = avgPrevious < avgVal ? 'up' : 'down';
            graphOptions.twoArrow = { direction: avgDir, outline: false, opacity: 0.3 };
        }
        $.normanBarChart('#graph', userVal, avgVal, graphOptions);
    },

	/**
	 * Attach the event handlers used by both question and answer states
	 */
	attachCommonEventHandlers: function() {
		var dashboard = this;
		
	    /*	
		$('#show_precise_graph').click(function(event){
			event.preventDefault();
			
			$(this).addClass('active').siblings().removeClass('active');
			//this.addClass('active');
						
			dashboard.isGraphAverage = false;
			dashboard.displayGraph( dashboard.currentIndicator() );
		});
		$('#show_average_graph').click(function(event){
			event.preventDefault();
			
			$(this).addClass('active').siblings().removeClass('active');
			
			dashboard.isGraphAverage = true;
			dashboard.displayGraph( dashboard.currentIndicator() );
		});
	    */	

        $('#welcome span').tooltip({
            tip: '#tooltip_container',
            position: ['bottom', 'center']
        });

        $('#settings').click(function(event){
            event.preventDefault();
            dashboard.createDialogs();
            var settingsDialog = $('#settings-dialog');
            $.getJSON($(this).attr('href'), {}, function(data, textStatus) { 
                settingsDialog.html(data.html); 
            });
            settingsDialog.dialog('open');
        });

        $('#settings-dialog, #survey-dialog').submit(function(event){
            event.preventDefault();
            dashboard.submitSettings( $(this) );
        });

        $('#invite').click( $.proxy(this.showInviteDialog, this) );
    },

    /**
     * Display the invite / spread-the-word dialog.
     */
    showInviteDialog: function (event) {
        event.preventDefault();
        var url = $(event.target).attr('href');
        this.createDialogs();
        $('#invite-dialog').dialog('open').load(url);
    },

    /**
     * Ajax submit the settings form, display any errors, close the dialog on success.
     */
    submitSettings: function (dialogDOM) {

        function onSuccess(data) {
            if ( data.close ) {
                dialogDOM.dialog('close');
            }
            else if (data.location) {
                window.location = data.location;
            }
            else {
                dialogDOM.html(data.html);
            }
        }

        dialogDOM.find('input[type="submit"]').replaceWith(GOODENERGY.Util.LOADING);
        GOODENERGY.Util.postForm(dialogDOM.find('form')[0], onSuccess, 'json');
    },

    showInitialSurvey: function() {
        this.createDialogs();
        var surveyDialog = $('#survey-dialog');
        $.getJSON($('#settings').attr('href')+'?survey=1', {}, function(data, textStatus) { 
            surveyDialog.html(data.html); 
        });
        surveyDialog.dialog('open');
    },

	/**
	 * Attach the event handlers for the question state
	 */
	 attachQuestionEventHandlers: function() {
	
		$('#question label').click(function(event) {
            $(this).closest('form').find('.wrong').hide(); 
		});
	
        $('#skip a').click(function(event) {
            event.preventDefault();
            $('#id_skip').val('1');
            $('#question').submit();
        });

        $('#question').submit(function(event){
            var form = $(this),
                isChecked,
                isNumbered;

            isChecked = form.find(':checked').length !== 0;
            isNumbered = $('#id_answer_number').val() !== '';
            if ( ! (isChecked || isNumbered) ) {
                event.preventDefault();
                form.find('.wrong').show(); 
            }
        });

		this.attachCommonEventHandlers();
	},
	
	/**
	 * Attach the event handlers for the answer state
	 */
	attachAnswerEventHandlers: function() {
		var dashboard = this,
	        /* for indicator_select */
            indicatorId,
            indicator;

		$('.indicator_select').click(function(event) {
			event.preventDefault();
			
			indicatorId = $(this).attr('rel');
			indicator = dashboard.indicatorsById[indicatorId];
			
			dashboard.currentIndex = $.inArray(indicator, dashboard.indicators);
			dashboard.displayResult(indicator);
		});
		
        /*
		$('#time_campaign').click(function(event) { 
			event.preventDefault();
			$(this).addClass('active').siblings().removeClass('active');
			dashboard.graphStartDate = dashboard.campaignStartDate;
			dashboard.graphEndDate = dashboard.campaignEndDate;
			dashboard.displayGraph( dashboard.currentIndicator() );
		});
		
		$('#time_month').click(function(event) {
			event.preventDefault();
			$(this).addClass('active').siblings().removeClass('active');
			
			var now = new Date();
			var nowUTC = Date.UTC(now.getFullYear(), now.getMonth(), now.getDate());
			var monthAgoUTC = nowUTC - GOODENERGY.ONE_MONTH_MILLIS;
			
			dashboard.graphStartDate = monthAgoUTC;
			dashboard.graphEndDate = nowUTC;
			
			dashboard.displayGraph(dashboard.currentIndicator());
		});
		
		$('#time_week').click(function(event) {
			event.preventDefault();
			$(this).addClass('active').siblings().removeClass('active');
			
			var now = new Date();
			var nowUTC = Date.UTC(now.getFullYear(), now.getMonth(), now.getDate());
			var weekAgoUTC = nowUTC - GOODENERGY.ONE_WEEK_MILLIS;
			
			dashboard.graphStartDate = weekAgoUTC;
			dashboard.graphEndDate = nowUTC;

			dashboard.displayGraph(dashboard.currentIndicator());
		});
	    */	
		this.attachCommonEventHandlers();
	}
	
};

$(function(){
    GOODENERGY.activeDashboard = new GOODENERGY.Dashboard();
});


/**
 * Good Energy Indicator model
 * @requires GOODENERGY
 */

/*global GOODENERGY */

if (typeof GOODENERGY === "undefined" || !GOODENERGY) {
    window.alert('Indicator.js expects GOODENERGY to be defined already');
}

/**
 * Indicator constructor
 */
GOODENERGY.Indicator = function(obj) {
    this.type = obj.display_type;
    this.updateAnswers(obj);
};

/**
 * Indicator body
 */
GOODENERGY.Indicator.prototype = {
	
	updateAnswers:
		function(answerObj) {
	
			this.userData = answerObj.from_data;
			this.meanData = answerObj.to_data;
			
			this.userAvgData = answerObj.from_avg_data;
			this.meanAvgData = answerObj.to_avg_data;
			
			this.userAverage = answerObj.from_average;
			this.groupAverage = answerObj.to_average;
			
			this.valueTicks = answerObj.value_ticks;
			this.valueLabels = answerObj.value_labels;
			this.hoverLabels = answerObj.hover_labels;
		}
		
};

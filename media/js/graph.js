/** Wrapper for flot.js, helps us draw nice graphs
 *
 * @requires GOODENERGY 
 */

/* jslint config */
/*global GOODENERGY */

if (typeof GOODENERGY === "undefined" || !GOODENERGY) {
    window.alert('GOODENERGY variable needs to be defined');
}

GOODENERGY.Graph = (function($){

    var MONTHS = ['Jan', 'Feb', 'March', 'April', 'May', 'June', 
            'July', 'Aug', 'Sept', 'Oct', 'Nov', 'Dec'],
        COLOR_USER = "#edbc28",
        COLOR_AVG = "#edbc28",
        COLOR_GROUP_AVG = "#60BEFF";

    function showTooltip(x, y, contents) {
        $('<div id="tooltip">' + contents + '</div>').css( {
            position: 'absolute',
            display: 'none',
            top: y - 15,
            left: x + 5,
            border: '1px solid #fdd',
            padding: '2px',
            'background-color': '#fee',
            opacity: 0.80
        }).appendTo("body").fadeIn(200);
    }

    function drawLine(plot, value, color, lineStyle) {
        
        if (value === 0) {
            // Don't draw lines right along the bottom of the graph
            return;
        }
        
        var canvas = plot.getCanvas(),
            offset = plot.getPlotOffset(),
            x = offset.left,
            y = plot.getAxes().yaxis.p2c(value) + offset.top,
            ctx = canvas.getContext("2d");

        ctx.save();
        
        ctx.globalCompositeOperation = 'destination-over';  // Draw under the data
        
        ctx.lineWidth = 2;
        ctx.strokeStyle = color;
        ctx.beginPath();
        
        if (lineStyle === 'straight') {
            ctx.moveTo(x, y);
            ctx.lineTo(plot.width() + offset.left, y);      
        }
        else if (lineStyle === 'dashed') {
        
            var width = ctx.canvas.width,
                height = ctx.canvas.height,
                lineX = x,
                dashWidth = 5,
                dashSpacing = 5;
            
            while (lineX + dashWidth < plot.width() + offset.left) {
                ctx.moveTo(lineX, y);
                
                lineX += dashWidth;
                ctx.lineTo(lineX, y);
                
                lineX += dashSpacing;
            }   
        }
        
        ctx.stroke();
        ctx.restore();
    }

    /**
    * Measures how big some text would be on the screen, in pixels.
    * @return A map with a 'height' and a 'width' key.
    */
    function measure(ctx, text, cssClass) {

        var tempContainer, jMeasure, result;

        tempContainer = '<div id="measure" style="float:left" class="'+ cssClass +'">'+ text +'</div>'; 
        $(ctx.canvas).after(tempContainer);
        jMeasure = $('#measure');

        result = {height: jMeasure.innerHeight(), width: jMeasure.innerWidth()};

        jMeasure.remove();
        return result;
    }

    /**
     * Display some text over the canvas.
     * 
     * @param ctx Canvas context
     * @param text The text to display
     * @param cssClass Class to apply to the div
     * @param x X position in page co-ordinates
     * @param y Y position in page coordinates
     * @return
     */
    function insertText(ctx, text, cssClass, x, y) {
        var html = '<div '+
                'style="position: absolute; left: '+ x +'px; top: '+ y +'px;"'+
                'class="'+ cssClass +'">';
        html += text +'</div>';
        $(ctx.canvas).after(html);  
    }

    /**
     * Convert canvas co-ordinates into page co-ordinates.
     * 
     * @param ctx Canvas context
     * @param x X in canvas coords
     * @param y Y in canvas coords
     * @return A map with x and y keys for page positions in pixels. 
     */
    function canvasToPage(ctx, x, y) {
        
        var pos = $(ctx.canvas).position();
        return {x: pos.left + x, y: pos.top + y};
    }

    /**
     * Convert page co-ordinates into canvas co-ordinates.
     * 
     * @param ctx Canvas context
     * @param x X in canvas coords
     * @param y Y in canvas coords
     * @return A map with x and y keys for canvas positions in pixels. 
     */
    function pageToCanvas(ctx, x, y) {

        var pos = $(ctx.canvas).offset();   // I don't know why this is offset() and canvasToPage is position()
        return {x: x - pos.left, y: y - pos.top};
    }
     
    function displayMessage(ctx, msg, cssClass) {
        
        var measurement = measure(ctx, msg, cssClass),
            coords = canvasToPage(ctx, ctx.canvas.width, ctx.canvas.height);

        insertText(
                ctx, 
                msg, 
                cssClass, 
                (coords.x - measurement.width) / 2, 
                (coords.y - measurement.height) / 2);
    }

    /**
     * Position the legend over the graph
     * 
     * @param plot The Flot plot object.
     * @param legendId Id of the dom element containing the legend
     * @param position 'left' or 'right'
     */
    function displayLegend(plot, legendId, position) {
        
        var offset = plot.getPlotOffset();
        
        var legendTable = $('#'+ legendId);
        legendTable.css('position', 'absolute');
        legendTable.css('display', 'block');
        legendTable.css('bottom', offset.bottom + 7);
        
        if (position === 'left') {
            legendTable.css('right', '');
            legendTable.css('left', offset.left + 11);   
        }
        else if (position === 'right') {
            legendTable.css('right', offset.right + 11);
            legendTable.css('left', '');
        }
        
    }

    /**
     * Main entry point to the module.
     */
    function populateGraph( graphId, 
                            data,
                            meanData,
                            legendId, 
                            user, 
                            baseline, 
                            norm, 
                            startDate,
                            endDate, 
                            noDataMsg,
                            valueTicksParam,
                            valueLabels,
                            hoverLabelsParam) {
        var hoverLabels;
        if (hoverLabelsParam) { 
            hoverLabels = hoverLabelsParam; 
        }
        else { 
            hoverLabels = valueLabels; 
        }

        var dataSeries = { label: user, data: data, color: COLOR_USER },
            meanDataSeries;
        if (meanData) {
            for (var i=0, len=meanData.length; i<len; i++) {
                var meanDataPoint = meanData[i];
                meanDataPoint[1] -= 0.1; /* Offset slightly so that overlapping dots are visible */
            }
            meanDataSeries = { label: 'Everyone', data: meanData, color: COLOR_GROUP_AVG }; 
        }

        var valueTicks;
        if (valueTicksParam) {
            valueTicks = valueTicksParam;
        }
        else {
            valueTicks = [];
            for (var i=0; i<=100; i += 10) {
                valueTicks.push(i);
            }
        }

        /* If we have text labels to display, display them as the second axis */
        /*
        if (valueTicks[0] !== valueLabels[0] && valueTicks[0]+'%' !== valueLabels[0]) {
            dataSeries.yaxis = 2;
        }
        */

        var formatter;
        if (valueLabels) {
            formatter = function(tickValue, axisObj) { 
                return valueLabels[ $.inArray(tickValue, valueTicks) ];
            };
        }
        else {
            formatter = function(tickValue, axisObj) { return tickValue + '%'; };
        }
        
        var options = {
            selection: { mode: "xy" },
            series: {
                lines: { show: true, lineWidth: 5 },
                points: { show: true },
                shadowSize: 5
            },
            grid: { hoverable: true, clickable: false, borderWidth: 1, borderColor: "#CCC" },
            legend: { show: false },    // We draw the legend ourselves
            xaxis: { mode: "time",
                     timeformat: "%d %b",
                     min: startDate,
                     max: endDate
                     },
            yaxis: { min: valueTicks[0], 
                     max: valueTicks[ valueTicks.length - 1],
                     ticks: valueTicks,
                     tickFormatter: formatter
                    }/*,
            y2axis: { min: valueTicks[0], 
                     max: valueTicks[ valueTicks.length - 1],
                     ticks: valueTicks
                    }*/
        };
 
        var plotObj, ctx;
        if (meanDataSeries) {
            plotObj = $.plot('#'+ graphId, [meanDataSeries, dataSeries], options);
        }
        else {
            plotObj = $.plot('#'+ graphId, [dataSeries], options);
        }
        ctx = plotObj.getCanvas().getContext("2d"); 

        /*
        if (data.length > 0) {
            if (baseline > 0) {
                drawLine(plotObj, baseline, COLOR_AVG, "straight");
            }
            drawLine(plotObj, norm, COLOR_GROUP_AVG, "straight");
        }
        else {
            displayMessage(ctx, noDataMsg, 'canvas-message');
        }
         */
        if (data.length === 0) {
            displayMessage(ctx, noDataMsg, 'canvas-message');
        }
        
        if (legendId) {
            /* Move the legend half way through campaign so as not to obscure too much data 
            var midDate = startDate + (endDate - startDate) / 2;
            var now = new Date();
            if (now < midDate) {*/
            
            displayLegend(plotObj, legendId, 'right');
            
            /*
            }
            else {
                displayLegend(plotObj, legendId, 'left');
            }
            */
        }
        
        var offset = plotObj.getPlotOffset();
        var normCanvasY = plotObj.getAxes().yaxis.p2c(norm) + offset.top;
        var baselineCanvasY = plotObj.getAxes().yaxis.p2c(baseline) + offset.top;
            
        var previousPoint = null;
        $('#graph').bind('plothover', function (event, pos, item) {
            $("#x").text(pos.x.toFixed(2));
            $("#y").text(pos.y.toFixed(2));

            var canvasPos = pageToCanvas(ctx, pos.pageX, pos.pageY);
            var onNorm = normCanvasY - 10 < canvasPos.y && canvasPos.y < normCanvasY + 10;
            var onBaseline = baselineCanvasY - 10 < canvasPos.y && canvasPos.y < baselineCanvasY + 10;
            
            if (item) {
                if (previousPoint !== item.datapoint) {
                    previousPoint = item.datapoint;
                    
                    $("#tooltip").remove();
                    var x = item.datapoint[0].toFixed(2);
                    var y = item.datapoint[1].toFixed(2);

                    var dt = new Date( Number(x) );
                    var day = dt.getUTCDate();
                    var month = MONTHS[ dt.getUTCMonth() ];
                    var dtString = month +' '+ day;
                    
                    var yNum = Number(y), 
                        label;
                    if ( $.inArray(yNum, valueTicks) === -1) {
                        label = yNum;
                        
                        /* If a percentage add % sign */
                        if ( $.inArray('%', hoverLabels[0]) !== -1 ) {
                            label += '%';
                        }
                    }
                    else {
                        label = hoverLabels[ $.inArray(yNum, valueTicks) ];
                    }
                    var display = dtString +': '+ label;
                    
                    showTooltip(item.pageX, 
                                item.pageY, 
                                display);
                }
            }
            /*
            else if (onNorm) {
                $("#tooltip").remove();
                showTooltip(pos.pageX, pos.pageY, 'Group Average');
            }
            else if (onBaseline) {
                $("#tooltip").remove();
                showTooltip(pos.pageX, pos.pageY, 'Your Average');
            }
            */
            else {
                $("#tooltip").remove();
                previousPoint = null;            
            }

        });
        
    }

    return {
        populateGraph: populateGraph
    };

})(jQuery);


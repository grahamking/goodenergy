
(function($) {

	var GOLDEN_RATIO = 1.61803399,
	    DASH_WIDTH = 5,
	    DASH_SPACING = DASH_WIDTH + 5;

	function insertText(ctx, text, color, x, y, extraStyle) {
		var html = '<div style="color: '+ color +';'+
            'position: absolute; '+
            'left: '+ x +'px; '+
            'top: '+ y +'px;';
        if (extraStyle) {
            html += extraStyle;
        }
        html += '">'+ text +'</div>';
		$(ctx.canvas).after(html);	
	}

	function drawLine(ctx, lineOptions, maxValue) {
	
		function drawSolidLine(value) {
		    
		    var height = ctx.canvas.height,
		        linePos = height * ((maxValue-value) / maxValue);
		    ctx.beginPath();
		    ctx.moveTo(0, linePos);
		    ctx.lineTo(ctx.canvas.width, linePos);
		    ctx.stroke();
		}
	
		function drawDashedLine(value) {
			
			var dashWidth = DASH_WIDTH,
			    dashSpacing = DASH_SPACING,
			    width = ctx.canvas.width,
			    height = ctx.canvas.height,
		        linePos = height * ((maxValue-value) / maxValue),
		        lineX = 0;

		    ctx.beginPath();
		    while (lineX + dashWidth < width) {
                ctx.moveTo(lineX, linePos);
                ctx.lineTo(lineX + dashWidth, linePos);
                lineX += dashSpacing;
		    }
		    ctx.stroke();
	
		}

        var lineY;

		if (! lineOptions) {
			return;
		}
		
		ctx.save();
		ctx.strokeStyle = lineOptions.color;
		if (lineOptions.lineStyle === 'dashed') {
			drawDashedLine(lineOptions.value);
		}
		else {
			drawSolidLine(lineOptions.value);
		}

        if (lineOptions.label) {
            lineY = ctx.canvas.height * (maxValue - lineOptions.value) / maxValue - 12;
            insertText(ctx, lineOptions.label, lineOptions.labelColor, 2, lineY, 'font-size: 85%;');
        }
		ctx.restore();
	}
	
	function canvasToPage(ctx, x, y) {
	
		var pos = $(ctx.canvas).position();
		return {x: pos.left + x, y: pos.top + y};
	}
	
	/**
	 * Measures how big some text would be on the screen, in pixels.
	 * @return A map with a 'height' and a 'width' key.
	 */
	function measure(ctx, text) {
	
		var measureDiv = '<div id="measure" style="float:left">'+ text +'</div>',
            jMeasure,
            result;

		$(ctx.canvas).after(measureDiv);
		jMeasure = $('#measure');
        result = {height: jMeasure.innerHeight(), width: jMeasure.innerWidth()};
		jMeasure.remove();
	
		return result;
	}
	
	function drawArrow(ctx, centerX, baseY, width, height, direction, outline, opacity) {
	
		ctx.save();
		
		var headHeight = height / (1 + GOLDEN_RATIO),
		    shaftHeight = headHeight * GOLDEN_RATIO,
            headSpace = width / (1 + GOLDEN_RATIO),
            shaftWidth = headSpace * GOLDEN_RATIO,
            headEdge = headSpace / 2,
		    baseX = centerX - shaftWidth / 2,
            scaleFactor = 0.5;

		if (baseY > ctx.canvas.height) {
			ctx.translate(baseX + (width * scaleFactor) / 3, baseY - height * scaleFactor);
			ctx.scale(scaleFactor, scaleFactor);
		}
		else {
			ctx.translate(baseX, baseY);
		}
		
		if (direction === 'down') {
			ctx.rotate(Math.PI);
			ctx.translate(-shaftWidth, height);
		}
		
		ctx.beginPath();
		ctx.moveTo(0, 0);
		ctx.lineTo(0, - shaftHeight);
		ctx.lineTo(- headEdge, - shaftHeight);
		ctx.lineTo(shaftWidth / 2, - shaftHeight - headHeight);
	
		ctx.lineTo(shaftWidth + headEdge, - shaftHeight);
		ctx.lineTo(shaftWidth, - shaftHeight);
		ctx.lineTo(shaftWidth, 0);
		
		ctx.closePath();
	
		if (outline) {
			ctx.stroke();
		}
		
		ctx.fillStyle = 'rgba(0, 0, 0, '+ opacity +')';
		ctx.fill();
		ctx.restore();
	}
	
	function drawBackground(ctx, options) {

        var lineVal = 1,
            backgroundGradient,
            lineIndex = 0,
            lineLabel = null,
            lineOptions;

		ctx.save();
		if (options.background.gradient) {
			backgroundGradient = ctx.createLinearGradient(
                    ctx.canvas.width / 2, 0, 
                    ctx.canvas.width / 2, ctx.canvas.height);
			backgroundGradient.addColorStop(0, options.background.color);
			backgroundGradient.addColorStop(1, options.background.gradient);
			ctx.fillStyle = backgroundGradient;
		}
		else {
			ctx.fillStyle = options.background.color;
		}
		ctx.fillRect(0, 0, ctx.canvas.width, ctx.canvas.height);
		
		if ( options.background.lines ) {
			while (lineVal < options.maxValue) {
                lineLabel = options.background.lineLabels && options.background.lineLabels[lineIndex];
                if (! lineLabel ) { lineLabel = lineVal; }
                lineOptions = {
                    value: lineVal, 
                    lineStyle: 'solid', 
                    color: options.background.lineColor, 
                    label: lineLabel,
                    labelColor: options.background.lineLabelsColor};
				drawLine(ctx, lineOptions, options.maxValue);
				lineVal += options.background.lineIncrement;
                lineIndex++;
			}
		}
		
		ctx.restore();	
	}
	
	function drawBar(ctx, value, xPos, width, color, outline, maxValue, legend, legendColor, arrowOptions) {
	
		ctx.save();
		
	    var height = ctx.canvas.height,
	        barHeight = height * (value / maxValue),
            barX = xPos - width / 2,
	        barY = height - barHeight,
            measurement,
            coords,
            /* Used only if arrowOptions is set */
		    arrowPadding = width * 0.2,	// 20% of bar width
		    arrowWidth = width / 2,
		    arrowX = xPos,
		    arrowHeight = 50,
		    arrowY = barY + arrowHeight + arrowPadding;

	    if ( outline ) {
	        ctx.fillStyle = 'black';
	        ctx.strokeRect(barX, barY, width, barHeight);
	    }
	
	    ctx.fillStyle = color;
	    ctx.fillRect(barX, barY, width, barHeight);
	
	    if (arrowOptions) {

		    if (arrowY > ctx.canvas.height) { // In case of small bar, reduce the padding to minimum
			    arrowY = barY + arrowHeight + 5;
		    }
		    drawArrow(ctx, 
                      arrowX, 
                      arrowY, 
                      arrowWidth, 
                      arrowHeight, 
                      arrowOptions.direction, 
                      arrowOptions.outline, 
                      arrowOptions.opacity);
	    }

        if (legend) {
            measurement = measure(ctx, legend);
            coords = canvasToPage(ctx, xPos, ctx.canvas.height);
            insertText(
                    ctx, 
                    legend, 
                    legendColor, 
                    coords.x - measurement.width / 2, 
                    coords.y - measurement.height);
        }
	    
	    ctx.restore();
	}

	function drawBarChart(ctx, one, two, options) {
	
        var maxValue = options.maxValue,
		    canvasWidth = ctx.canvas.width - options.paddingLeft,
            padding = options.padding,	
            quarter = canvasWidth / 4,
            width = canvasWidth / 2 - (padding + padding / 2);
	
		drawBackground(ctx, options);
		drawLine(ctx, options.baseline, maxValue);

	    drawBar(ctx, 
                one, 
                quarter + padding / 2 + options.paddingLeft, 
                width, 
                options.one.color, 
                options.outline, 
                maxValue, 
                options.one.legend, 
                options.one.legendColor, 
                options.oneArrow);
        drawBar(ctx, 
                two, 
                quarter * 3 - padding / 2 + options.paddingLeft, 
                width, 
                options.two.color, 
                options.outline, 
                maxValue, 
                options.two.legend, 
                options.two.legendColor, 
                options.twoArrow);
    
	    drawLine(ctx, options.target, maxValue);
	}
	/*
	function drawLegend(ctx, options) {
	
		ctx.strokeStyle = 'black';
		
		var section = ctx.canvas.width / 2;
		var y = ctx.canvas.height / 2;
	
		var canvasMinX = $(ctx.canvas).offset().left;	// Postion of the canvas in page co-ordinates
	    var canvasMinY = $(ctx.canvas).offset().top;
	
		$('#legend').after('<div id="measure_me">ABC</div>');
		var wordHeight = $('#measure_me').innerHeight();
		$('#measure_me').remove();
		
		legendLine(ctx, options.baseline.color, options.baseline.lineStyle, 
					section / 2, y, section, y);
		insertText('legend', 'Baseline', canvasMinY + wordHeight /1.5, 10);
	
		legendLine(ctx, options.target.color, options.target.lineStyle,
					section + section / 2, y, 2 * section, y);
		insertText('legend', 'Target', canvasMinY + wordHeight /1.5, section + 10);
		
		var padding = 5;
	
		legendRect(ctx,
                    2 * section + section / 2, 
                     padding, 
                     section / 2, 
                     ctx.canvas.height - padding * 2,
                     options.one.color,
                     options.outline);
        insertText('legend', 'Me', canvasMinY + wordHeight /1.5, 2*section + 10);
        
        legendRect(ctx,
                    3 * section + section / 2, 
                    padding, 
                    section / 2 - padding, 
                    ctx.canvas.height - padding * 2,
                    options.two.color,
                    options.outline);
        insertText('legend', 'Others', canvasMinY + wordHeight /1.5, 3*section + 10);
		
	}
	*/
	function legendLine(ctx, color, lineStyle, startX, startY, endX, endY) {
	
		ctx.save();
		
		ctx.beginPath();
		ctx.strokeStyle = color;
		if (lineStyle === 'dashed') {
			var lineX = startX;
			while (lineX + DASH_WIDTH < endX) {
                ctx.moveTo(lineX, startY);
                ctx.lineTo(lineX + DASH_WIDTH, endY);
                lineX += DASH_SPACING;
		    }
		}
		else {
			ctx.moveTo(startX, startY);
			ctx.lineTo(endX, endY);
		}
		ctx.stroke();
	
		ctx.restore();	
	}
	
	function legendRect(ctx, x, y, width, height, color, outline) {
		ctx.save();
		ctx.strokeStyle = 'black';
		if (outline) {
			ctx.strokeRect(x, y, width, height);
		}
		ctx.fillStyle = color;
		ctx.fillRect(x, y, width, height);
		ctx.restore();	
	}
	
    /**
     * Borrowed from flot, jQuery / Canvas graphing library.
     * Dynamically creates the canvas element, and patches it up to work with excanvas for IE.
     */
    function constructCanvas(placeholder) {
        function makeCanvas(width, height) {
            var c = window.document.createElement('canvas');
            c.width = width;
            c.height = height;
            if ($.browser.msie) {   // excanvas hack
                c = window.G_vmlCanvasManager.initElement(c);
            }
            return c;
        }
        
        var canvas, canvasWidth, canvasHeight;

        canvasWidth = placeholder.width();
        canvasHeight = placeholder.height();
        placeholder.html(""); // clear placeholder
        /*
        if (placeholder.css("position") === 'static') {
            placeholder.css("position", "relative"); // for positioning labels and overlay
        }
        */
        if (canvasWidth <= 0 || canvasHeight <= 0) {
            throw "Invalid dimensions for plot, width = " + canvasWidth + ", height = " + canvasHeight;
        }

        if ($.browser.msie) {   // excanvas hack
            window.G_vmlCanvasManager.init_(window.document); // make sure everything is setup
        }
        
        // the canvas
        canvas = $(makeCanvas(canvasWidth, canvasHeight)).appendTo(placeholder).get(0);
        return canvas;
    }

	$.normanBarChart = function(canvasContainer, leftVal, rightVal, options) {
	    
	    var placeholder = $(canvasContainer),
		    ctx,
            defaults,
            opts,
            canvas;
		
        canvas = constructCanvas(placeholder);
        ctx = canvas.getContext('2d');

		/*
		var canvasMinX = $(canvas).offset().left;
	    var canvasMaxX = canvasMinX + $(canvas).width();
	    var canvasMinY = $(canvas).offset().top;
	        
	    $(canvas).click(function(evt) {
	        
	        var canvasHitX = evt.pageX - canvasMinX;
	        var canvasHitY = evt.pageY - canvasMinY;
	        
	        if (evt.pageX > canvasMinX && evt.pageX < canvasMaxX && window.console) {
	          console.log('click');
	        }
	    });
		*/
	
        /* Example defaults - all possible values 
		defaults = {
			maxValue: 100,
			padding: 30,
			outline: true,
			one: { color: '#7395bf', legend: 'Me 75%', legendColor: 'white' },
			two: { color: '#92d050', legend: 'Others 60%', legendColor: 'black' },
			background: { color: 'white', gradient: 'grey', lines: true, lineColor: '#ede', lineIncrement: 10 },
			oneArrow: { direction: 'up', outline: false, opacity: 0.5 },
			twoArrow: { direction: 'down', outline: false, opacity: 0.5 },
			baseline: { value: 47, color: 'black', lineStyle: 'dashed' },
			target: { value: 80, color: 'orange', lineStyle: 'solid' }
		}; */
        defaults = { padding: 30, outline: true, paddingLeft: 0 };
		opts = $.extend(defaults, options);

        /* Correct max value 
        opts.maxValue = Math.max(leftVal, rightVal) + options.background.lineIncrement; */
		drawBarChart(ctx, leftVal, rightVal, opts);

		/*
		var legendCanvas = document.getElementById('legend');
		drawLegend(legendCanvas.getContext('2d'), options);
		*/
	    
    };

})(jQuery);

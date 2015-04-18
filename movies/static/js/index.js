function Collage($selector, provider, fill_speed, min_width, min_height){
	var nx, ny, n, areas, full_areas, full_areas_x, filling;
	function get_areas(row, col, w, h){
		var ret=[], position=row*nx+col, w=Math.min(w, nx-col), inc=nx-w;
		while (h-->0){
			for (var i=w; i>0; i--) ret.push(position++);
			position+=inc;
			if (position>=n) break;
		}
		return ret;
	}
	function get_empty_areas(positions){
		var ret=0, len=positions.length;
		while (len-->0) 
			if (!areas[positions[len]]) ret+=1;
		return ret;
	}
	function fill_areas(positions){
		for (var len=positions.length; len>0; )
			areas[positions[--len]]=true
	}
	function add(w, h){
		w = Math.floor(w/min_width);
		h = Math.floor(h/min_height);		

		var ret, len=0, max=w*h;
		if (max){
			var row = Math.floor(Math.random()*ny);
			var col=Math.floor(Math.random()*nx);

			for (var i=0; i<n; i++){
				var positions=get_areas(row, col, w, h);
				var empty = get_empty_areas(positions);
				if (empty > len){
					ret=[positions, row, col]
					if (empty===max) break;
					len=empty;
				}
				if (++col===nx) {
					col=0;
					if (++row===ny) row=0;
				}
			}
			if (ret){
				fill_areas(ret[0]);
				return [ret[2]*min_width, ret[1]*min_height]
			}
		} 
	}
	function autofill(){
		var filling_check;
		function step(){
			if (filling === filling_check){
				var size=provider.get();
				if (size){
					var position = add(size[0], size[1]);
					if (position) {
						provider.put(filling, position[0], position[1]);
						setTimeout(step, fill_speed);
					} 
				} 
			} 
		}
		filling = filling_check = 'pc'+new Date().getTime();
		step();
	}
	this.restart = function(){
		autofill();
	}
	this.resize = function(){
		var new_nx = Math.ceil($selector.width()/min_width);
		var new_ny = Math.ceil($selector.height()/min_height);
		if (nx===undefined || new_ny > ny || new_nx > nx){
			nx = new_nx;
			ny = new_ny;
			n = new_nx * new_ny;
			areas = new Array(n);
			autofill();
		}
	}

	this.resize();
}


function setupIndex($body){
    $('#imdb_search').click(showImdbChoice);
	var $collage=$('<div id="collage"></div>').appendTo($body);
    $.get('/ax_covers').done(function(data){
    	if (data.covers){
    		var covers=data.covers, minw=17, minh=12, len=covers.length, current=0, oldClass;
    		function Provider(){
    			this.get = function(){
					for (var i=0; i<len; i++){
						var cover=covers[current], w=cover[1], h=cover[2];
						if (w>=minw && h>=minh) return [w, h];
						if (++current===len) current=0;
					}    			
    			}
    			this.put=function(putClass, x, y){
    				if (oldClass!==putClass){
    					$('.'+oldClass).hide('slow', function(){this.remove();});
    					oldClass=putClass;
    				}
    				$('<img src="'+covers[current][0]+'">').appendTo($collage).offset({ top: y, left: x }).addClass(putClass);
					if (++current===len) current=0;
    			}
    		}
		   	var collage = new Collage($collage, new Provider(), 1, minw, minh);
		   	$(window).resize(collage.resize);
    	}
    });
}

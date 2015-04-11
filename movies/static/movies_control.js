function setupMoviesControl() {

	function create_cell_filter(exact, td, val){
		var ltd=td, lval=val;
		if (exact) return function(tds){
			return lval===$(tds[ltd]).text();
		}
		return function(tds){
			return $(tds[ltd]).text().indexOf(lval)>=0;
		}
	}

	function create_filter(){
		var effective=[];
		for (var each in filters){
			var filter=filters[each];
			var val = filter[0].val();
			if (val){
				effective.push(create_cell_filter(filter[2], filter[1], val));
			}
		}
		$('table#movies_control tbody tr').each(function(){
			var $tr=$(this);
			var tds=$tr.children(), ok=true;
			for (var e in effective){
				if (!effective[e](tds)){
					ok=false;
					break;
				}
			}
			if (ok) $tr.show(); else $tr.hide();
		});
	}

	function fill_combobox($combobox, content_class, splitter){
		var ret={}
		$(content_class).each(function(){
			var text=$.trim($(this).text());
			if (text){
				if (splitter){
					text.split(splitter).forEach(function(v){if (v) ret[v]=true;});
				} else {
					ret[text]=true;
				}
			}
		});
		$combobox.append($("<option></option>"));
		Object.keys(ret).sort().forEach(function(v) {
        	$combobox.append($("<option></option>").text(v));
       });
	}

	var $title=$('#title-filter').change(create_filter);
	var $year=$('#year-filter').change(create_filter);
	var $genres=$('#genres-filter').change(create_filter);
	var $location=$('#location-filter').change(create_filter);
	var $audios=$('#audios-filter').change(create_filter);
	var $subs=$('#subs-filter').change(create_filter);
	var $actor1=$('#actor1-filter').change(create_filter);
	var $actor2=$('#actor2-filter').change(create_filter);

	var lang_splitter=/\s*\/\s*/, br_splitter=/\s+/;	
	var filters=[
		[$title, 1, false],
		[$year, 2, true],
		[$genres, 3, false],
		[$audios, 4, false],
		[$subs, 5, false],
		[$location, 6, true],
		[$actor1, 7, false],
		[$actor2, 7, false],
	];

	fill_combobox($year, '.ic_year');
	fill_combobox($genres, '.ic_genres', br_splitter);
	fill_combobox($audios, '.ic_audios', lang_splitter);
	fill_combobox($subs, '.ic_subs', lang_splitter);
	fill_combobox($location, '.ic_location');

}

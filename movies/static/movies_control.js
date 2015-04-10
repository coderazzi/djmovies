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
			//console.log(ok);
		});
	}

	function fill_combobox($combobox, content_class, split){
		var ret={}
		$(content_class).each(function(){
			var text=$.trim($(this).text());
			if (text){
				if (split){
					text.split(splitter).forEach(function(v){ret[v]=true;});
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
	var $format=$('#format-filter').change(create_filter);
	var $location=$('#location-filter').change(create_filter);
	var $audios=$('#audios-filter').change(create_filter);
	var $subs=$('#subs-filter').change(create_filter);

	var splitter=/\s*\/\s*/;	
	var filters=[
		[$title, 1, false],
		[$year, 2, true],
		[$format, 4, true],
		[$audios, 5, false],
		[$subs, 6, false],
		[$location, 7, true],
	];

	fill_combobox($year, '.ic_year');
	fill_combobox($format, '.ic_format');
	fill_combobox($audios, '.ic_audios', true);
	fill_combobox($subs, '.ic_subs', true);
	fill_combobox($location, '.ic_location');

}

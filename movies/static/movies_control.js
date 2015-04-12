function setupMoviesControl() {
	handle_movies_control_filtering();
	handle_movies_control_info();
}

function handle_movies_control_info(){
	var $dialog, $title, $img, $year, $genre, $actors, $duration, 
		$duration_imdb, $links, $format, $audio, $subs;
	function show_modal(){
		if (! $dialog) {
			$dialog=$('#dialog_movie_info');
			$title=$('h4', $dialog);
			$img=$('img', $dialog);
			$year=$('#dmi_year', $dialog);
			$genre=$('#dmi_genre', $dialog);
			$actors=$('#dmi_actors', $dialog);
			$duration=$('#dmi_duration', $dialog);
			$duration_imdb=$('#dmi_duration_imdb', $dialog);
			$links=$('#dmi_links', $dialog);
			$format=$('#dmi_format', $dialog);
			$audio=$('#dmi_audio', $dialog);
			$subs=$('#dmi_subs', $dialog);
		}
		var tds=$(this).closest('tr').children();
		var duration=$(tds[9]).text().split('/');
		$title.text($(tds[1]).text());
		$dialog.modal('show');
		$img.attr('src', $('img', $(tds[0])).attr('src'));
		$year.text($(tds[2]).text());
		$genre.html($(tds[3]).html());
		$actors.html($(tds[7]).html());
		$duration.text(duration[0]);
		$duration_imdb.text(duration[1]);	
		$links.html($(tds[10]).html());		
		$format.text($(tds[8]).text());
		$audio.text($(tds[4]).text());
		$subs.text($(tds[5]).text());
	}
	$('.ic_cover').click(show_modal);
	$('.ic_title').click(show_modal);
}

function handle_movies_control_filtering(){

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


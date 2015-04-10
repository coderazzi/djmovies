function setupMoviesControl() {
	function create_filter(){

	}
	var like_filters={
		1 : $('#title-filter').change(create_filter), //second td in rows
	}
	var exact_filters={
		2: $('#year-filter').change(create_filter),
		$('#format-filter').change(create_filter),
		$('#audios-filter').change(create_filter),
		$('#subs-filter').change(create_filter),
		$('#location-filter').change(create_filter),
	};
}
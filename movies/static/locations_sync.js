function setupLocationsSync(){

	function imdbDialogCallback(filepath, mediainfo, imdbUrl){
		console.log('filepath:'+filepath);
		console.log('mediainfo:'+mediainfo);
		console.log('imdbUrl:'+imdbUrl);
			Messenger().post("Your request has succeded!");
	}

	$('.search_path').click(function(){
		var path = $('.path', $(this).parent().parent());
		if (path.length){
			showImdbDialog(path.text(), imdbDialogCallback);
		} 
		return false;
	});
}
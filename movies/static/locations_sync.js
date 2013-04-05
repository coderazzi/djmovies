function setupLocationsSync(){

	function imdbDialogCallback(filepath, mediaInfo, imdbInfo){
		console.log('filepath:'+filepath);
		console.log('mediainfo:'+mediaInfo);
		console.log('imdbInfo:'+imdbInfo);

		// Messenger().run({
		// 	errorMessage: 'Error destroying alien planet',
		// 	successMessage: 'Alien planet destroyed!',
		// 	action: function(opts) {
		// 		if (++i < 3) {
		// 			return opts.error({
		// 				status: 500,
		// 				readyState: 0,
		// 				responseText: 0
		// 			});
		// 		} else {
		// 			return opts.success();
		// 		}
		// 	}
		// });

		Messenger().post("Your request has succeded!", type='progress');
	}

	$('.search_path').click(function(){
		// Messenger().post({
		// 	progressMessage:"Your request has succeded!", 
		// 	type:'progress'
		// });
		var path = $('.path', $(this).parent().parent());
		if (path.length){
			showImdbDialog(path.text(), imdbDialogCallback);
		} 
		return false;
	});
}
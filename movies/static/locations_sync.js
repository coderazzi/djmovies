function setupLocationsSync(){

	function imdbDialogCallback(info){
		// console.log('filepath:'+filepath);
		// console.log('mediainfo:'+mediaInfo);
		// console.log('imdbInfo:'+imdbInfo);

		ajaxPost({
			url: '/locations_sync_update',
			message: 'Adding movie information',
			data: info
		});
	}

	$('.search_path').click(function(){
		// Messenger().post({
		// 	progressMessage:"Your request has succeded!", 
		// 	type:'progress'
		// });
		var path = $('.path', $(this).parent().parent());
		if (path.length){
			ImdbDialog.show(path.text(), imdbDialogCallback);
		} 
		return false;
	});
}
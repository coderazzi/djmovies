function setupLocationsSync(){

	function imdbDialogCallback(filepath, mediainfo, imdbinfo){
		// console.log('filepath:'+filepath);
		// console.log('mediainfo:'+mediaInfo);
		// console.log('imdbInfo:'+imdbInfo);

		ajaxPost({
			url: '/locations_sync_update',
			message: 'Adding movie information',
			data:{
				filepath: filepath,
				mediainfo: mediainfo,
				imdbinfo: imdbinfo,
			}
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
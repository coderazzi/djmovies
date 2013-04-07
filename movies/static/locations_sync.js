function setupLocationsSync(){

	function searchPathCallback(){
		var $tr=$(this).parent().parent();
		var path = $('.path', $tr);
		if (path.length){
			ImdbDialog.show(path.text(), function(info){
				ajaxPost({
					url: '/locations_sync_update',
					message: 'Adding movie information',
					data: info,
					success: function(response){
						$tr.html(response);
						$('.search_path', $tr).click(searchPathCallback);
					}
				});
			});
		} 
		return false;
	}

	$('.search_path').click(searchPathCallback);
}
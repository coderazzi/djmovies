function setupLocationsSync(){

	function addPathCallback(){
		var $tr=$(this).parent().parent();
		var path = $('.path', $tr);
		if (path.length){
			ImdbDialog.show(path.text(), function(info){
				ajaxPost({
					url: '/locations_sync_update',
					message: 'Adding movie information',
					data: info,
					success: function(response){
						$tr.addClass('location_updated').html(response);
						$('.add_path', $tr).click(addPathCallback);
					}
				});
			});
		} 
		return false;
	}

	$('.add_path').click(addPathCallback);
}
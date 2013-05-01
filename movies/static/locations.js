function setupLocations(){

	var $dialog = $('#input_path').on('shown', function(){
		$("input", $dialog).focus(); //just focus the input component		
	}).on('show', function(){
		addProgressToModal($dialog);
	}).on('hidden', function(){
		//just in case a submit is going on
		window.stop(); //ie seems to require window.document.execCommand('Stop');
	});	

	$('.add_path').click(function(){
		var currentLocation = $(this).attr('data-location');
		if (currentLocation){
			$('#input_path_id', $dialog).val(currentLocation);
			$('#input_path').modal();
		}
		return false;
	});
	
}

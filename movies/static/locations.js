function setupLocations(){
	var $dialog = $('#edit-location').on('shown.bs.modal', function(){
		$name.focus(); //just focus the input component		
	}).on('show.bs.modal', function(){
		addProgressToModal($dialog);
	}).on('hidden.bs.modal', function(){
		//just in case a submit is going on
		window.stop(); //ie seems to require window.document.execCommand('Stop');
	});	

	var $title=$('#dialog-title', $dialog);
	var $id=$('input[name="location.id"]', $dialog);
	var $name=$('input[name="location.name"]', $dialog);
	var $desc=$('input[name="location.description"]', $dialog);
	var $path=$('input[name="location.path"]', $dialog);

	function edit_location(){
		var $this=$(this);
		var currentLocation = $this.attr('data-location');
		if (currentLocation) {
			$title.html('Edit location');
			var tds = $this.closest('tr').children();
			$id.val(currentLocation);
			$name.val($(tds[1]).text());
			$desc.val($(tds[2]).text());
			$path.val($(tds[3]).text());
		} else {
			$title.html('Add new location');
			$id.val('');
			$name.val('');
			$desc.val('');
			$path.val('');
		}
		$dialog.modal('show');
		return false;		
	}

	$('.edit-location').click(edit_location);
	$('#add-location-btn').click(edit_location);
	$('.click-tr-ref').click(function(){
		Spinner.show();
		window.location=$(this).closest('tr').attr('data-href');
	})
}

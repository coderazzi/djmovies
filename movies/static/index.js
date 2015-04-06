function setupIndex($body){

    var $dialog;

    function show_locations(){
        if (! $dialog) {
            $dialog=$('#locations_selection');           
            var $select=$('select', $dialog);
            var $enter=$('.btn-primary', $dialog);
            //if users presses ENTER on select, just click the select button
            $select.keypress(function (e) {
				if(e.which== 13) {
					$enter.click();
					return false;  
				}
			}); 
			//have the focus on location selection
            $dialog.on('shown.bs.modal', function(){$select.focus();});
            $enter.click(function(){
            	window.location.href='/location/'+$select.val();
            });
        }
        $dialog.modal('show');
        return false;
    }

    $('#icon_locations').click(show_locations);
}
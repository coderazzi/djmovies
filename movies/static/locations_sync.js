function setupLocationsSync(){

	var $problemDialog = $('#locations_sync_problems_dialog');

	var $subtitleDialog, $subtitlePathText, $subTitlePathInput, $subtitleLanguage, $subtitleMovie;
	var $subtitleEditionTr;

	function addPathCallback(){
		var $tr=$(this).parent().parent();
		var path = $('.path', $tr);
		if (path.length){
			DialogImdb.show(path.text(), function(info){
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

	function editSubtitleCallback(){
		//var $this=$(this); //the edit icon associated to the subtitle
		$subtitleEditionTr=$(this).parent().parent(); //group, td, tr
		//we need to find the associated movie if
		var $mainTr=$subtitleEditionTr, movieId;
		while (!movieId && ($mainTr=$mainTr.prev()).length){
			movieId=$mainTr.attr('data-movie-id');
		}

		if (!$subtitleDialog){
			$subtitleDialog = $('#locations_subtitle_dialog').on('shown', subTitleDialogShownCallback);
			$subtitlePathText = $('.path', $subtitleDialog);
			$subtitleLanguage = $('select', $subtitleDialog).val('English');
			$subtitleMovie = $('input[name="movie.id"]', $subtitleDialog);
			$subtitlePathInput = $('input[name="file.path"]', $subtitleDialog);
			setupAjaxModal($subtitleDialog, {
				success: function(response){
					$subtitleDialog.modal('hide');
					$subtitleEditionTr.replaceWith(response);
					$('.edit_subtitle').off('click').click(editSubtitleCallback);
				}
			});
		}

		var $path=$subtitleEditionTr.find('.path'), language=$path.attr('data-language'), path=$.trim($path.text());
		$subtitlePathText.text(path);
		$subtitlePathInput.val(path);
		$subtitleMovie.val(movieId);
		if (language) $subtitleLanguage.val(language);
		$subtitleDialog.modal('show');
		return false;
	}

	function subTitleDialogShownCallback(){
		$subtitleLanguage.focus();
	}

	if ($('td', $problemDialog).length){
		$problemDialog.modal('show');
	}
	$('.add_path').click(addPathCallback);
	$('.edit_subtitle').click(editSubtitleCallback);
}
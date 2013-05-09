function setupLocationsSync($locationsSyncSelector){

	var $problemDialog = $('#locations_sync_problems_dialog');

	var $subtitleDialog, $subtitlePathText, $subTitlePathInput, $subtitleLanguage, $subtitleMovie;
	var $subtitleEditionTr;

	var locationId, urlRemoveSubtitle, urlEditMovie;

	function setupSubtitleHandlers(){
		$('.edit_subtitle').off('click').click(editSubtitleCallback);
		$('.remove_subtitle').off('click').click(removeSubtitleCallback);
	}

	function editMovieCallback(){
		var $tr=$(this).parent().parent();
		var path = $('.path', $tr), title=$('.title', $tr);
		if (path.length){
			DialogImdb.show(
				path.text(), 
				$tr.attr('data-movie-id'), 
				title && title.text(),
				function(info){
				ajaxPost({
					url: urlEditMovie,
					message: 'Adding movie information',
					data: info,
					success: function(response){
						//we remove the existing TR, but also any following TRs
						//containing no data-movie-id attribute (or subtitle class)
						var $next=$tr.next();
						while ($next.length && $next.hasClass('subtitle')){
							var $rem = $next;
							$next = $next.next();
							$rem.remove();
						}
						$tr.replaceWith(response);
						$('.edit-movie').off('click').click(editMovieCallback);
						setupSubtitleHandlers();
					}
				});
			});
		} 
		return false;
	}

	function removeSubtitleCallback(){
		$subtitleEditionTr=$(this).parent().parent(); //group, td, tr
		var $mainTr=$subtitleEditionTr, movieId;
		while (!movieId && ($mainTr=$mainTr.prev()).length){
			movieId=$mainTr.attr('data-movie-id');
		}

		var path=$.trim($subtitleEditionTr.find('.path').text())

		DialogConfirm.show('Are you sure to remove from database the subtitle '+path+'?',
			{
				url:urlRemoveSubtitle,
				success: function(response){
					$subtitleEditionTr.html('');
					DialogConfirm.hide();
				},
				message:'Subtitle database deletion',
				data:{
					movieId:movieId,
					locationId: locationId,
					path:path
				}
			});
		return false;
	}

	function editSubtitleCallback(){
		$subtitleEditionTr=$(this).parent().parent(); //group, td, tr
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
				message: 'Subtitle update',
				success: function(response){
					$subtitleDialog.modal('hide');
					$subtitleEditionTr.replaceWith(response);
					setupSubtitleHandlers();
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


	locationId = $locationsSyncSelector.attr('data-location-id');
	urlRemoveSubtitle = $locationsSyncSelector.attr('data-remove-subtitle-url');
	urlEditMovie = $locationsSyncSelector.attr('data-edit-movie-url');

	if ($('td', $problemDialog).length){
		$problemDialog.modal('show');
	}
	$('.edit-movie').click(editMovieCallback);
	setupSubtitleHandlers();
}
function setupLocationsSync($locationsSyncSelector){

	var $problemDialog = $('#locations_sync_problems_dialog');

	var $subtitleDialog, $subtitleTitleText, $subtitlePathText, $subtitlePathInput;
	var $subtitleLanguage, $subtitleMovie, $subtitleSubmitButton, $subtitleNormalize;	
	var $subtitle
	var $editionTr;

	var locationId, subtitleDialogSettings;
	var urlEditSubtitle, urlFetchSubtitle, urlRemoveSubtitle, urlEditMovie, urlRemoveMovie;

	function setupEventHandlers(){
		$('.edit-movie').click(editMovieCallback);
		$('.remove-movie').click(removeMovieCallback);
		$('.edit-subtitle').off('click').click(editSubtitleCallback);
		$('.remove-subtitle').off('click').click(removeSubtitleCallback);
		$('.fetch-subtitle').off('click').click(fetchSubtitleCallback);
	}

	function updateMovieInfo($tr, html){
		var $next=$tr.next();
		while ($next.length && $next.hasClass('subtitle')){
			var $rem = $next;
			$next = $next.next();
			$rem.remove();
		}
		if (html){
			$tr.replaceWith(html);
			setupEventHandlers();
		} else {
			$tr.remove();
		}

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
						updateMovieInfo($tr, response);
					}
				});
			});
		} 
		return false;
	}

	function removeMovieCallback(){
		$editionTr=$(this).parent().parent(); 

		var movieId=$editionTr.attr('data-movie-id');
		var title=$.trim($editionTr.find('.title').text())

		DialogConfirm.show('Are you sure to remove from database the movie '+title+'?',
			{
				url:urlRemoveMovie,
				success: function(response){
					updateMovieInfo($editionTr);
					DialogConfirm.hide();
				},
				message:'Movie deletion',
				data:{
					movieId:movieId,
					locationId: locationId
				}
			});
		return false;
	}

	function removeSubtitleCallback(){
		$editionTr=$(this).parent().parent(); 
		var $mainTr=$editionTr, movieId;
		while (!movieId && ($mainTr=$mainTr.prev()).length){
			movieId=$mainTr.attr('data-movie-id');
		}

		var path=$.trim($editionTr.find('.path').text())

		DialogConfirm.show('Are you sure to remove from database the subtitle '+path+'?',
			{
				url:urlRemoveSubtitle,
				success: function(response){
					$editionTr.html('');
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


	function setupSubtitleDialog(callback, forFetching){
		if (!$subtitleDialog){
			$subtitleDialog = $('#locations_subtitle_dialog').on('shown', function(){$subtitleLanguage.focus();});
			$subtitleTitleText = $('.title', $subtitleDialog);
			$subtitlePathText = $('.path', $subtitleDialog);
			$subtitleLanguage = $('select', $subtitleDialog).val('English');
			$subtitleNormalize = $('.checkbox', $subtitleDialog);
			$subtitleMovie = $('input[name="movie.id"]', $subtitleDialog);
			$subtitlePathInput = $('input[name="file.path"]', $subtitleDialog);
			$subtitleSubmitButton = $('button[type="submit"]', $subtitleDialog);
			subtitleDialogSettings = setupAjaxModal($subtitleDialog, {}).settings;
		}
		if (forFetching){
			subtitleDialogSettings.message='Subtitles fetch';
			subtitleDialogSettings.url = urlFetchSubtitle;
			$subtitlePathInput.val('');
			$subtitlePathText.hide();
			$subtitleTitleText.show();
			$subtitleNormalize.hide();
			$subtitleSubmitButton.text('Fetch subtitles');
		} else {
			subtitleDialogSettings.message='Subtitle update';
			subtitleDialogSettings.url = urlEditSubtitle;
			$subtitlePathText.show();
			$subtitleTitleText.hide();
			$subtitleNormalize.show();
			$subtitleSubmitButton.text('Update');
		}
		subtitleDialogSettings.success = callback;
	}

	function editSubtitleCallback(){
		function success(response){
			$subtitleDialog.modal('hide');
			$editionTr.replaceWith(response);
			setupEventHandlers();			
		}

		$editionTr=$(this).parent().parent(); //group, td, tr

		var $mainTr=$editionTr,
			$path=$editionTr.find('.path'), 
		    language=$path.attr('data-language'), 
		    path=$.trim($path.text()),
		    movieId;

		while (!movieId && ($mainTr=$mainTr.prev()).length){
			movieId=$mainTr.attr('data-movie-id');
		}

		setupSubtitleDialog(success, false);
		$subtitlePathText.text(path);
		$subtitlePathInput.val(path);
		$subtitleMovie.val(movieId);
		if (language) $subtitleLanguage.val(language);
		$subtitleDialog.modal('show');
		return false;
	}

	function fetchSubtitleCallback(){
		function success(response){
			updateMovieInfo($editionTr, response);
			$subtitleDialog.modal('hide');
		}

		setupSubtitleDialog(success, true);

		$editionTr=$(this).parent().parent(); //group, td, tr
		$subtitleTitleText.text($('.title', $editionTr).text());
		$subtitleMovie.val($editionTr.attr('data-movie-id'));
		$subtitleDialog.modal('show');
		return false;
	}


	locationId = $locationsSyncSelector.attr('data-location-id');
	urlEditSubtitle = $locationsSyncSelector.attr('data-edit-subtitle-url');
	urlFetchSubtitle = $locationsSyncSelector.attr('data-fetch-subtitle-url');
	urlRemoveSubtitle = $locationsSyncSelector.attr('data-remove-subtitle-url');
	urlEditMovie = $locationsSyncSelector.attr('data-edit-movie-url');
	urlRemoveMovie = $locationsSyncSelector.attr('data-remove-movie-url');

	if ($('td', $problemDialog).length){
		$problemDialog.modal('show');
	}
	setupEventHandlers();
}
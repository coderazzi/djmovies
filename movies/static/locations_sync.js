function setupLocationsSync($locationsSyncSelector){

	var $problemDialog = $('#locations_sync_problems_dialog');

	var $stDialog, $stTitleText, $stPathText, $stPathInput;
	var $stLanguage, $stMovie, $stNormalize;	

	var $fetchDialog, $fetchTitleText;
	var $fetchLanguage, $fetchMovie, $fetchSelection;	
	
	var $updatingTr;

	var locationId, fetchingMatches;
	var urlRemoveSubtitle, urlEditMovie, urlRemoveMovie;

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
		$updatingTr=$(this).parent().parent(); 

		var movieId=$updatingTr.attr('data-movie-id');
		var title=$.trim($updatingTr.find('.title').text())

		DialogConfirm.show('Are you sure to remove from database the movie '+title+'?',
			{
				url:urlRemoveMovie,
				success: function(response){
					updateMovieInfo($updatingTr);
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
		$updatingTr=$(this).parent().parent(); 
		var $mainTr=$updatingTr, movieId;
		while (!movieId && ($mainTr=$mainTr.prev()).length){
			movieId=$mainTr.attr('data-movie-id');
		}

		var path=$.trim($updatingTr.find('.path').text())

		DialogConfirm.show('Are you sure to remove from database the subtitle '+path+'?',
			{
				url:urlRemoveSubtitle,
				success: function(response){
					$updatingTr.html('');
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
		if (!$stDialog){
			$stDialog = $('#locations_subtitle_dialog').on('shown', function(){$stLanguage.focus();});
			$stPathText = $('.path', $stDialog);
			$stLanguage = $('select', $stDialog).val('English');
			$stNormalize = $('.checkbox', $stDialog);
			$stMovie = $('input[name="movie.id"]', $stDialog);
			$stPathInput = $('input[name="file.path"]', $stDialog);
			setupAjaxModal($stDialog, {
				message : 'Subtitle update',
				success : function(response){
					$stDialog.modal('hide');
					$updatingTr.replaceWith(response);
					setupEventHandlers();								
				}
			});
		}

		$updatingTr=$(this).parent().parent(); //group, td, tr

		var $mainTr=$updatingTr,
			$path=$updatingTr.find('.path'), 
		    language=$path.attr('data-language'), 
		    path=$.trim($path.text()),
		    movieId;

		while (!movieId && ($mainTr=$mainTr.prev()).length){
			movieId=$mainTr.attr('data-movie-id');
		}

		$stPathText.text(path);
		$stPathInput.val(path);
		$stMovie.val(movieId);
		if (language) $stLanguage.val(language);
		$stDialog.modal('show');
		return false;
	}

	function fetchSubtitleCallback(){
		if (!$fetchDialog){
			$fetchDialog = $('#locations_subtitle_fetch_dialog').on('shown', function(){
				$fetchSelection.focus();
				dialogSettings.submit.click();
			});
			$fetchTitleText = $('.title', $fetchDialog);
			$fetchLanguage = $('select[name="language"]', $fetchDialog).val('English');
			$fetchSelection = $('select[name="subtitle"]', $fetchDialog);
			$fetchMovie = $('input[name="movie.id"]', $fetchDialog);
			var dialogSettings = setupAjaxModal($fetchDialog, {
				message : 'Subtitles fetch',
				success : function(response){
					if (fetchingMatches){
						fetchingMatches=false;
						$fetchSelection.html(response);
					} else {
						updateMovieInfo($updatingTr, response);
					}
					dialogSettings.hideProgress();
				}
			});
		}

		fetchingMatches=true;
		$updatingTr=$(this).parent().parent();
		$fetchTitleText.text($('.title', $updatingTr).text());
		$fetchSelection.html('');
		$fetchMovie.val($updatingTr.attr('data-movie-id'));
		$fetchDialog.modal('show');
		return false;
	}


	locationId = $locationsSyncSelector.attr('data-location-id');
	urlRemoveSubtitle = $locationsSyncSelector.attr('data-remove-subtitle-url');
	urlEditMovie = $locationsSyncSelector.attr('data-edit-movie-url');
	urlRemoveMovie = $locationsSyncSelector.attr('data-remove-movie-url');

	if ($('td', $problemDialog).length){
		$problemDialog.modal('show');
	}
	setupEventHandlers();
}
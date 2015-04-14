function setupUquery($body){
	//information on how long time has passed since last refresh
	$('.timeago').timeago();	

	var $addQueryModal=$('#add-query-modal').on('shown.bs.modal', function () {
    	$addquery.focus();
	});

	var $addquery=$('input[name="add-query"]');
	var $addqueryform=$addquery.closest('form').submit(function(){
		var txt = $addquery.val().trim();
		if (!txt) {
			$addquery.focus();
		} else {
			$addQueryModal.modal('toggle');
			Spinner.show();
			$.post(BASE_UQUERY_URL, {query:txt})
			 .done(function(data){window.location.href = UQUERY_URL+data.query_id;})
			 .fail(function(data){alert_server_error();})
			 .always(function(){Spinner.hide();});
		}
		return false;		
	});

	$('#add-query-btn').click(function(){$addQueryModal.modal()});

	function requery_all(){
		$.get(MAIN_UQUERY_URL+'/requery_info').done(function(data){
		 	if (data){
		 		$requery_placeholder.html('<p>Checking now <b>'+data.title+
		 			'</b>&hellip;&nbsp; <span class="glyphicon glyphicon-refresh spinning" aria-hidden="true"></span></p>');
		 		$.post(UQUERY_URL+data.id+'/refresh').done(function(results){
		 			if (results.new_results>0){
		 				window.location.href = UQUERY_URL+data.id;
		 			} else {
		 				requery_all();
		 			}
		 		}).error(function(){
		 			$requery_placeholder.html('<p>Error contacting server.</p>')		
		 		});
		 	}
		 	else {
		 		$requery_placeholder.html('<p>Nothing to recheck at the moment.</p>')
		 	}
		 }).error(function(){
			$requery_placeholder.html('<p>Error contacting server.</p>')
		});
	}

	var $requeryModal=$('#requery-modal').on('shown.bs.modal', requery_all);
	var $requery_placeholder=$('#requery-placeholder');

	$('#requery-btn').click(function(){$requeryModal.modal()});

	$('.btn-delete').click(function(){
		var $tr=$(this).closest('tr');
		swal({   
			title: "Are you sure?",   
			text:  "This query will not be available any longer!",   
			type: "warning",   
			showCancelButton: true,   
			confirmButtonClass: "btn-danger",
			confirmButtonText: "Yes, delete it",   
			}, 
			function(confirmed){   
				if (confirmed){
					var queryId=$tr.attr('data-query-id');
					$.ajax(UQUERY_URL+queryId+'/delete', {type:'DELETE'})
					.done(function(data){
						if (data && data.ok) {
							$tr.hide('slow', function(){ $tr.remove(); });
						} else {
							alert_server_error()
						}
					})
					.fail(function(){
						alert_server_error();
					});		
				}
			});		
	});
}

// Module used on query.html / query_base.html
function setupUqueryResults($body){

	UQUERY_DOWNLOAD_STATUS={NO_DOWNLOADED:0xc0, DOWNLOADED:0xc1, BAD_DOWNLOAD:0xc9, WRONG_RESULT:0xcf}; //same as in logic.py

	//We need 2 global variables in this module:
	// -query id, read from the <body>
	// -the current filter, which can persist if a refresh if done
	var query_id=$body.attr('data-query-id'), current_filter='';

	init();

	//method to be called whenever the #results info (query_base) changes
	//it setups all the event handlers and initializes any required variables
	function init(){

		//When user presses submit, the form is not post; instead, we
		//post is as ajax, and if everything works well, the result will
		//be a direct replacement of the #results div (that contains all the results)
		var $refreshForm=$('#refresh-form').submit(function(){
			Spinner.show();
			$.post($refreshForm.attr('action'), $refreshForm.serialize())
			 .done(function(data){
			 	//Return value is (json) the number of new results
			 	var new_results=data.new_results;
			 	if (new_results){			 		
			 		//if there are new results, we invoke ajax again, to get
			 		//the html content for the new #results
			 		$.get(UQUERY_URL+query_id+'/base')
			 		 .done(function(data){
			 		 	//we replace the #results and show the number of new results
			 		 	$('#results').replaceWith(data);
						swal({   
							title: "Info",   
							text:"There are "+new_results +" new result(s)",
							type: "info"
						});
			 		 	init();
			 		 })
			 		 .fail(function(){alert_server_error();})
			 		 .always(function(){Spinner.hide()});
			 	} else {
			 		//if there are no new results, just show the info
					Spinner.hide();
					swal({   
						title: "Info",   
						text:"There are no new results",
						type: "info",   
						timer: 3000
					});
			 	}
			 })
			 .fail(function(){Spinner.hide();alert_server_error();});
			return false;
		});

		//handle event - user setting query as 'complete' -> invoke server
		$('#completed-status').change(function(){
			var $this=$(this), completed=this.checked;
			var error_function=function(){
				$this.prop('checked', !completed);
				alert_server_error();				
			}
			$.post(UQUERY_URL+$this.attr('data-id')+'/set-completed', {completed: completed}).done(function(data){
				if (!data || !data.ok) error_function();
			}).fail(error_function);		
		});

		//handle event - user showing/hiding the NFO info
		$('.nfo-checkbox input').change(function(){
			//We obtain the first ancestor with class 'row', and then go to next row
			//which we toggle (show/hide)
			$(this).closest('.row').next().toggle('show');
		});

		//handle event - user checking/unchecking the 'bad results' checkbox, which updates the status
		$('.result-status').change(function(){
			update_status(this, this.checked? UQUERY_DOWNLOAD_STATUS.BAD_DOWNLOAD : UQUERY_DOWNLOAD_STATUS.DOWNLOADED);
		});

		//handle event - user claiming a result to belong to another query. We verify first if
		//the user is right
		$('.wrong-query').change(function(){
			var self=this;
			swal({   
				title: "Are you sure?",   
				text:  "This result will not be available any longer!",   
				type: "warning",   
				showCancelButton: true,   
				confirmButtonClass: "btn-primary",//"#DD6B55",   
				confirmButtonText: "Yes, wrong result",   
				 }, 
				function(confirmed){   
					//if the user is right, we update the status to WRONG_RESULT 
					//(which effectively removes the row from the listing)
					$(self).prop('checked', false);
					if (confirmed) update_status(self, UQUERY_DOWNLOAD_STATUS.WRONG_RESULT);
				});		
		});

		//handle event: user resulting a item: it updates the status of the query to
		//DOWNLOADED -and the result itself is handled by the form, (www.binsearch.info)
		$('.btn-download').click(function(){
			update_status(this, UQUERY_DOWNLOAD_STATUS.DOWNLOADED);
			return true;
		});

		//information on how long time has passed since last refresh
		$('.timeago').timeago();	

		//initialize filters
		init_filters();
	}


	//filters correspond to the selection of results per size
	//it requires a global variable, current_filter.
	//the filter SELECT includes one show all option, with VAL='', and one
	//OPTION per found size, in this case the VAL is directly the size, such as
	// '4' or '4-nfo'. Note that all rows with class row-status have a data-filter that
	// matches this string
	function init_filters(){
		var filters={}, $filter=$('#size-filter');

		//applyFilter means hiding/showing all rows that do not match the given filter
		function applyFilter(){
			//note that we update current-filter with the user's selection
			current_filter=$("option:selected", $filter).val();
			$('.row-status').each(function(i, el){
				var $row=$(el);
				if (current_filter==='' || current_filter===$row.attr('data-filter')){
					$row.show('slow');
				} else {
					$row.hide('slow');
				}				
			});			
		}

		//invoke applyFilter whenever the filter changes
		$filter.change(applyFilter);

		//now we find all sizes. The unique values will be used to populate the
		//SELECT filter
		$('.row-status').each(function(i, el){
			var $row=$(el);
			filters[$row.attr('data-filter')]=true;
			status_updated($row, parseInt($row.attr('data-status')));
		});

		filters = Object.keys(filters).sort().reverse();
		for (var each in filters){
			var f = filters[each];
			$filter.append($("<option />").val(f).text('Show only size '+f).prop('selected', f===current_filter));
		}

		//finally, the current_filter is already applied.
		//this means that when we replace the div #results on a refresh action, the filter can be persisted
		if (current_filter) applyFilter();
	};

	//method to update the status of a result. The first variable is a DOM element belonging to the row(s)
	//of the given result
	function update_status(element, status){
		//the main info on the result is given on the parent row, with class row-status
		var $row=$(element).closest('.row-status');
		var oid=$row.attr('data-oid');
		var error_function=function(){
			status_updated($row, parseInt($row.attr('data-status')));
			alert_server_error();			
		}
		$.post(MAIN_UQUERY_URL+'/result/'+query_id+'/'+oid+'/set-status', {status: status})
			.done(function(data){
				if (!data || !data.ok){
					error_function();
				}
				else if (status===UQUERY_DOWNLOAD_STATUS.WRONG_RESULT){ 
					//for this status, we remove directly the row
					//this means that no row has ever this status
					$row.hide('slow', function(){ $row.remove(); });
					var $result=$('#n-results');
					$result.html(parseInt($result.html())-1);
				} else {
					//for other values, we update the status 
					$row.attr('data-status', status);
					//and change the info shown to the user
					status_updated($row, status);
				}
			})
			.fail(error_function);
	};


	//method to reflect the status of a result, depending on the status
	function status_updated($row, status){
		var $resultButton=$($row.find('input[type="submit"]'));
		var $statusCheckbox=$($row.find('.result-status'));
		var $statusLabel=$($statusCheckbox.parent());
		if (status===UQUERY_DOWNLOAD_STATUS.NO_DOWNLOADED){
			$resultButton.val('Download');
			$resultButton.addClass('btn-primary');
			$statusLabel.addClass('unknown-result');
		} else {
			$resultButton.val('Download (again)');
			$resultButton.removeClass('btn-primary');
			$statusLabel.removeClass('unknown-result');
			if (status==UQUERY_DOWNLOAD_STATUS.DOWNLOADED){
				$statusCheckbox.prop('checked', false);
				$statusLabel.removeClass('bad-result');
			} else { //UQUERY_DOWNLOAD_STATUS.BAD_DOWNLOAD
				$statusCheckbox.prop('checked', true);
				$statusLabel.addClass('bad-result');
			}
		}
	};
}
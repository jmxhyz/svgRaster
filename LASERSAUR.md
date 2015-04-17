The current version of the LasaurApp doesn't have a good way to send your own custom gcode.  The following html/javascript can be added to add a gcode tab that will allow you to paste gcode and send it.  Due to to some errors when sending too much gcode at once the javascript breaks it up into 5000 line chunks and sends it one chunk at a time.

You can insert the following code in frontend/app.html at line 330 after the following line:
</div> <!-- end of log tab -->

'''
                            <!--  START   CUSTOM GCODE TAB -->
                            <div id='tab_gcode' class='tab-pane'>
                                <div id='gcode_content'>
                                    <textarea id='gcode_edit' style='clear:both; width: 900px;' rows=20></textarea>
                                    <button id="gcode_submit" class="btn btn-large btn-primary">Send to Lasersaur</button>
                                </div>
                            </div>

                            <script>
				var chunksize = 5000;
				var gqueue = Array();
				function queue_gcode(gcode){
					var tmp = gcode.split("\n");
					var chunk = "";
					var lc = 0;
					for (var i=0; i<tmp.length; i++){
						lc++;
						chunk += tmp[i]+"\n";
						if (lc>=chunksize){
							gqueue.push(chunk);
							lc=0;
							chunk=""
						}	
					}
					if (chunk.length>0){ gqueue.push(chunk); }	
				}

				function process_gcode_queue(){
				
					if (progress_not_yet_done_flag==false && gqueue.length > 0){
						gcode = gqueue.shift();
						progress_not_yet_done_flag=true;
						send_gcode(gcode, "New Chunk from Queue Sent.", true);	
					}
					setTimeout("process_gcode_queue()",5000);	
				}
				setTimeout("process_gcode_queue()",5000);
				
				$("#cancel_btn").click(function(e){
					gqueue = Array();
				});

                                $('.tabs-left ul').append('<li><a href="#tab_gcode" id="tab_gcode_button" data-toggle="tab"><i class="icon-exclamation-sign" style="margin-right:2px"></i> Gcode</a></li>');
                                $("#gcode_submit").click(function(e) {
                                    var gcode = $('#gcode_edit').val();
                                    if (gcode){
                                        //send_gcode(gcode, "G-Code sent to backend.", true);
                                        queue_gcode(gcode); 
				    }
                                });
                            </script>
                            <!-- END      CUSTOM GCODE TAB -->
'''

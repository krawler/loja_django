function getNextStep(status){
        
    switch(status){
        case 'A': return 'Preparando';
        case 'C': return 'Aprovado';
        case 'R': return 'Criado';
        case 'P': return 'Enviado';
        case 'E': return 'Finalizado';
        case 'F': return 'Preparando';
    }
}
function getStatusNameExtenso(sigla){

    switch(sigla){
        case 'A': return 'Aprovado';
        case 'C': return 'Criado';
        case 'R': return 'Reprovado';
        case 'P': return 'Preparando';
        case 'E': return 'Enviado';
        case 'F': return 'Finalizado';
    }
}

function showDialogModalStatus(id, status, token){
        
    $.ajaxSetup({
        headers:
        { 'X-CSRF-TOKEN': $('meta[name="csrf-token"]').attr('content') }
    });
    
    $('.btnChangeStatus').on('click', function(){
        var de = $(this).attr('data-status');
        var url = $(this).attr('data-url');
        var para = getNextStep(de);

        jQuery('#dialog-confirm-status').dialog({
            resizable: false,
            height: "auto",
            width: 400,
            modal: true,
            buttons: {
                "Mudar situação": function() {
                    $.ajax({
                            type: "POST",
                            dataType: "json",
                            url: url,
                            data: {
                                "pedidoid" : id,
                                "de": de,
                                "para" : para,
                                "csrfmiddlewaretoken": $('meta[name="csrf-token"]').attr('content')
                            },
                            success: function(jsonData) { 
                                status_pedido  = '#status_' + id;
                                $(status_pedido).html(getStatusNameExtenso(jsonData)); 
                                $('#'+id).parent().children().eq(2).html(getStatusNameExtenso(jsonData));
                                return jsonData;
                            }
                        });
                        $( this ).dialog( "close" );
                },
                Cancel: function() {                        
                    $( this ).dialog( "close" );
                }
            }
        });
    });
}

function showDialogModalDeactivate(id){
    $('.btn-delete').on('click', function(){
        
        var url = $(this).attr('url');
        $("#dialog-confirm-deactivate").dialog({
            resizable: false,
            height: "auto",
            width: 400,
            modal: true,
            buttons: {
                    "Desativar": function() {
                        $.ajax({
                            type: "POST",
                            dataType: "json",
                            url: url,
                            data: {
                                "pedidoid" : id,
                                "csrfmiddlewaretoken": $('meta[name="csrf-token"]').attr('content')
                            },
                            success: function(jsonData) { 
                                window.location.href = '/pedido/tabela';    
                            }
                        });
                    $( this ).dialog( "close" );

                },
                Cancel: function() {
                    $( this ).dialog( "close" );
                }
            }
        });
    });
}

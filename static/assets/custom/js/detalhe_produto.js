$(document).ready(function(){

$("#descricao_longa").find("p").addClass("lead");

$("#imagem_produto").ezPlus({
    zoomType: "inner",
    cursor: "pointer",
    zoomWindowFadeIn: 500,
    zoomWindowFadeOut: 750
}); 
    
Fancybox.bind('[data-fancybox="gallery"]', {}); 
    
    /*
    $(".imagem_variacao").hover(function(){
        $("#imagem_produto").removeData('elevateZoom');
        $("#imagem_produto").attr("src", $(this).attr("data-zoom-image"));
        $("#imagem_produto").data("zoom-image", $(this).attr("data-zoom-image"));
        $("#imagem_produto").ezPlus({
            zoomType: "inner",
            cursor: "pointer",
            zoomWindowFadeIn: 500,
            zoomWindowFadeOut: 750
        }); 
        
    });
    */
    estoques = JSON.parse($('#estoques_variacoes').val());
    saldo_estoque = estoques[$("#select-variacoes").val()];
    $("#saldo_estoque").html(saldo_estoque);
    if(saldo_estoque === 0){
        $("#pergunta_aviso_produto_disponivel").show();
        $("#btnAdicionarCarrinho").addClass('disabled');
    }    

    dimensoesVariacoes = $('#dimensoes').val().replaceAll('\'', '"')
    dimensoesVariacoes = JSON.parse(dimensoesVariacoes);

    $("#select-variacoes").change(function(){
        id_variacao = $(this).val();
        if(estoques[id_variacao] === 0){
            $("#pergunta_aviso_produto_disponivel").show();
            $("#btnAdicionarCarrinho").addClass('disabled');
        }else{
            $("#btnAdicionarCarrinho").removeClass('disabled');
            $("#pergunta_aviso_produto_disponivel").hide();
        }

        $("#saldo_estoque").html(estoques[id_variacao]);

        for(dimensao in dimensoesVariacoes){
            if(dimensoesVariacoes[dimensao].id == $("#select-variacoes").val()){
                $("#desc_largura").html(dimensoesVariacoes[dimensao].largura);
                $("#desc_comprimento").html(dimensoesVariacoes[dimensao].comprimento);
                $("#desc_altura").html(dimensoesVariacoes[dimensao].altura);
                $("#desc_peso").html(dimensoesVariacoes[dimensao].peso);
            }
                
        }
    });

    $("#sim_produto_disponivel").click(function(){

        id_variacao = $(this).data("variacaoid");
    
        url = $(this).data("url");
    
        $.ajax({
            type: "POST",
            dataType: "json",
            url: url,
            data: {
                "id_variacao" : id_variacao,
                "csrfmiddlewaretoken": $('meta[name="csrf-token"]').attr('content')
            },
            success: function(jsonData) { 
                if(jsonData=="True")
                    return console.log("returned: " + jsonData);
            }
        });
    
        $("#pergunta_aviso_produto_disponivel").html("Você receberá um email quando esse produto estiver disponível em estoque")
    
    });
    
});
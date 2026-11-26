function value = gallery_color(role, sample)
% Shared with the Python gallery. Preserve the data-driven color pivot.
persistent catalog
if isempty(catalog)
    catalog = jsondecode(fileread(fullfile(fileparts(mfilename('fullpath')), 'figure-palette.json')));
end
if strcmp(role,'categorical')
    value = cell2mat(cellfun(@hex_rgb,catalog.categorical(:),'UniformOutput',false));
elseif strcmp(role,'sequential') || strcmp(role,'signed')
    anchors = cell2mat(cellfun(@hex_rgb,catalog.(role)(:),'UniformOutput',false));
    if strcmp(role,'signed')
        sample = (sample+1)/2;
    end
    value = interp1(linspace(0,1,size(anchors,1)),anchors,min(1,max(0,sample)));
else
    value = hex_rgb(catalog.colors.(role));
end
end

function color = hex_rgb(hex)
color = sscanf(hex(2:end),'%2x%2x%2x',[1 3])/255;
end

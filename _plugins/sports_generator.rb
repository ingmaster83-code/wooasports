require 'json'

module Jekyll
  class SportsPageGenerator < Generator
    safe true
    priority :normal

    def generate(site)
      facilities = site.data['facilities']
      return unless facilities&.any?

      Jekyll.logger.info "SportsGenerator:", "#{facilities.size}개 페이지 생성 중..."

      completeness = lambda do |s|
        ['address', 'phone', 'homepage', 'area'].count { |k| s[k] && s[k] != '' && s[k] != '0' }
      end

      facilities.each do |f|
        same_region = facilities
          .select { |s| s['region'] == f['region'] && s['slug'] != f['slug'] }
          .sort_by { |s| -completeness.call(s) }
          .first(8)
          .map { |s| { 'slug' => s['slug'], 'name' => s['name'], 'city' => s['city'], 'typeLabel' => s['ftype'], 'typeIcon' => s['typeIcon'] } }

        same_type = facilities
          .select { |s| s['ftype'] == f['ftype'] && s['slug'] != f['slug'] }
          .sort_by { |s| -completeness.call(s) }
          .first(8)
          .map { |s| { 'slug' => s['slug'], 'name' => s['name'], 'region' => s['region'], 'city' => s['city'] } }

        region_ordered = facilities
          .select { |s| s['region'] == f['region'] }
          .sort_by { |s| [s['ftype'].to_s, s['name'].to_s] }
        idx = region_ordered.index { |s| s['slug'] == f['slug'] }
        prev_spot = nil
        next_spot = nil
        if idx && region_ordered.size > 1
          p = region_ordered[(idx - 1) % region_ordered.size]
          n = region_ordered[(idx + 1) % region_ordered.size]
          prev_spot = { 'slug' => p['slug'], 'name' => p['name'] }
          next_spot = { 'slug' => n['slug'], 'name' => n['name'] }
        end

        site.pages << FacilityPage.new(site, f, same_region, same_type, prev_spot, next_spot)
      end

      by_region = facilities.group_by { |f| f['region'] }
      by_region.each do |region, region_facilities|
        slug = region_facilities.first['regionSlug']
        site.pages << RegionPage.new(site, region, slug, region_facilities)
      end

      by_type = facilities.group_by { |f| f['ftype'] }
      by_type.each do |ftype, type_facilities|
        slug = type_facilities.first['typeSlug']
        icon = type_facilities.first['typeIcon']
        site.pages << TypePage.new(site, ftype, slug, icon, type_facilities)
      end

      site.pages << SearchIndexPage.new(site, facilities)

      Jekyll.logger.info "SportsGenerator:", "완료 (#{facilities.size}개, #{by_region.size}개 지역, #{by_type.size}개 종목)"
    end
  end

  class FacilityPage < Page
    def initialize(site, f, same_region, same_type, prev_spot, next_spot)
      @site = site
      @base = site.source
      @dir  = "facility/#{f['slug']}"
      @name = 'index.html'

      self.process(@name)
      self.read_yaml(File.join(@base, '_layouts'), 'facility.html')
      self.data.merge!(f)
      self.data['layout']       = 'facility'
      self.data['facilityName'] = f['name']
      self.data['typeLabel']    = f['ftype']
      self.data['same_region']  = same_region
      self.data['same_type']    = same_type
      self.data['prev_spot']    = prev_spot
      self.data['next_spot']    = next_spot

      self.data['title'] = "#{f['name']} 위치·이용안내 | #{f['region']} #{f['city']} #{f['ftype']}"
      self.data['description'] = "#{f['name']}(#{f['region']} #{f['city']}) #{f['ftype']} 위치, 연락처, 관리기관 정보를 확인하세요."
    end
  end

  class RegionPage < Page
    def initialize(site, region, slug, facilities)
      @site = site
      @base = site.source
      @dir  = "region/#{slug}"
      @name = 'index.html'

      self.process(@name)
      self.read_yaml(File.join(@base, '_layouts'), 'region.html')
      self.data['layout']      = 'region'
      self.data['region']      = region
      self.data['regionSlug']  = slug
      self.data['facilities']  = facilities
      self.data['title']       = "#{region} 공공체육시설 총정리 | 축구장·테니스장·수영장 #{facilities.size}곳"
      self.data['description'] = "#{region} 공공체육시설 #{facilities.size}곳 총정리! 축구장·테니스장·수영장·체육관 위치를 한눈에 확인하세요."
    end
  end

  class TypePage < Page
    def initialize(site, ftype, slug, icon, facilities)
      @site = site
      @base = site.source
      @dir  = "type/#{slug}"
      @name = 'index.html'

      self.process(@name)
      self.read_yaml(File.join(@base, '_layouts'), 'type.html')
      self.data['layout']      = 'type'
      self.data['typeLabel']   = ftype
      self.data['typeSlug']    = slug
      self.data['typeIcon']    = icon
      self.data['facilities']  = facilities
      self.data['title']       = "전국 #{ftype} 목록 #{facilities.size}곳"
      self.data['description'] = "전국 #{ftype} #{facilities.size}곳 목록. 지역별 #{ftype} 위치 정보를 확인하세요."
    end
  end

  class SearchIndexPage < Page
    def initialize(site, facilities)
      @site = site
      @base = site.source
      @dir  = ''
      @name = 'search_index.json'

      self.process(@name)
      self.data = { 'layout' => nil, 'sitemap' => false }

      index = facilities.map do |f|
        { 'slug' => f['slug'], 'name' => f['name'], 'region' => f['region'], 'city' => f['city'], 'typeLabel' => f['ftype'] }
      end

      self.content = index.to_json
    end

    def output = self.content
    def render(layouts, registers); end
  end
end

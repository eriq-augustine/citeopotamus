#!/usr/bin/perl
use strict;
use warnings;

use Carp;
use Cwd;
use File::Copy;

use constant ROOT_DIR => getcwd().'/data/';

sub dir_status {
   if ($ENV{DEBUG}) {
      print("current directory: ".getcwd()."\n");
   }
}

sub read_dir {
   my ($dir_handle) = @_;

   return grep { $_ !~ m/[.]+/ } readdir($dir_handle);
}

sub dir_map {
   my ($success, $dir_name, $anon_func) = (0, @_);

   if (-d $dir_name && chdir($dir_name)) {
      dir_status();
      &$anon_func();
      $success = 1;
      chdir(q{..});
      dir_status();
   }

   return $success;
}

sub get_ref_stats {
   my ($REF_ROOT, $max_citation, $num_citations) = @_;
   my ($global_max, $global_count) = (0, 0);

   opendir(my $REF_DIR, getcwd()) or croak('Unable to open current directory');

   my $DIR_BEGIN = telldir($REF_DIR);

   # A loop to pull all sub directories up to current directory
   for my $sub_dir (read_dir($REF_DIR)) {
      dir_map($sub_dir, sub {
         my ($tmp_max, $tmp_count) = get_ref_stats($REF_ROOT, $max_citation, $num_citations + 1);
         #print("max ref: $tmp_max\ncitation count: $tmp_count\n");

         if ($global_max < $tmp_max) { $global_max = $tmp_max; }
         if ($global_count < $tmp_count) { $global_count = $tmp_count; }
      });
   }
   closedir($REF_DIR);

   opendir($REF_DIR, getcwd()) or croak('Unable to open current directory');

   my $sub_dir_name = q{};
   for my $sub_dir (read_dir($REF_DIR)) {
      if (-d $sub_dir) {
         $sub_dir_name = $sub_dir;

         if ($sub_dir_name =~ m/\/(\d+)$/) {
            my $dir_name = $1;
            #print ("dir name: $dir_name\n");

            if ($max_citation < $dir_name) {
               $max_citation = $dir_name;
            }
         }

      }
   }

   closedir($REF_DIR);

   if ($global_max < $max_citation) { $global_max = $max_citation; }
   if ($global_count < $num_citations) { $global_count = $num_citations; }

   return ($global_max, $global_count);
}

sub fix_ref_dir {
   my ($paper_dir) = @_;
   my ($max_cite, $cite_count) = (0, 0);

   my $success = dir_map("$paper_dir/references", sub {
      my $reference_root = getcwd();
      opendir(my $REF_DIR, $reference_root) or croak('Unable to open cwd');

      for my $sub_dir (read_dir($REF_DIR)) {
         if (-d $sub_dir) {
            my $sub_dir_name = $sub_dir;
            $cite_count++;

            if ($max_cite < $sub_dir) {
               $max_cite = $sub_dir;
            }
         }
      }
      closedir($REF_DIR);

      chdir(q{..});
   });

   #print "$paper_dir: [$max_cite, $cite_count]\n";

   if (!$success) {
      print({*STDERR} "Failed to map function on dir $paper_dir/references\n");
   }

   return ($max_cite, $cite_count);
}

sub main {
   my ($paper_list, $stat_aggr) = ({}, {});
   my $aggr_count = 0;

   if (chdir(ROOT_DIR)) {
      opendir(my $DIR_HANDLE, getcwd()) or croak('Unable to open directory '.
                                                 ROOT_DIR);

      for my $paper_dir (read_dir($DIR_HANDLE)) {
         chomp($paper_dir);

         if ($paper_dir !~ m/dynamo/ && -d $paper_dir) {
            if ($ENV{DEBUG}) { print("fixing $paper_dir\n"); }

            my ($max_cite, $cite_count) = fix_ref_dir($paper_dir);
            #print "max: $max_cite\ncount: $cite_count\n";

            $paper_list->{$paper_dir} = [$max_cite, $cite_count];

            if ($stat_aggr->{max}) {
               $stat_aggr->{max} += $max_cite;
            }
            else { $stat_aggr->{max} = $max_cite; }

            if ($stat_aggr->{count}) {
               $stat_aggr->{count} += $cite_count;
            }
            else { $stat_aggr->{count} = $cite_count; }

            if ($stat_aggr->{miss}) {
               $stat_aggr->{miss} += ($max_cite - $cite_count);
            }
            else { $stat_aggr->{miss} = ($max_cite - $cite_count); }

            $aggr_count++;
         }

      }

      closedir($DIR_HANDLE);
   }
   else { print({*STDERR} "Unable to chdir to ".ROOT_DIR."\n"); }

   print("num_papers: $aggr_count\n");
   for my $stat (keys %{$stat_aggr}) {
      print("$stat: ".($stat_aggr->{$stat}/$aggr_count)."\n");
   }

   for my $paper (keys %{$paper_list}) {
      print("$paper: [max - $paper_list->{$paper}->[0]], ".
            "[count - $paper_list->{$paper}->[1]]\n");
   }
}

main();
